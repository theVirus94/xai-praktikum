from get_data import get_loader
from utils.vector_utils import  values_target, weights_init, vectors_to_images_coco, noise_coco
from evaluation.evaluate_generator_coco import calculate_metrics_coco
from logger import Logger
from utils.explanation_utils import get_explanation, explanation_hook_coco
from torch.autograd import Variable
from torch import nn
import torch
import time


class Experiment:
    """ The class that contains the experiment details """
    def __init__(self, experimentType):
        """
        Standard init
        :param experimentType: experiment enum that contains all the data needed to run the experiment
        :type experimentType:
        """
        self.name = experimentType.name
        self.type = experimentType.value
        #print(self.type)
        self.explainable = self.type["explainable"]
        self.explanationType = self.type["explanationType"]
        self.generator = self.type["generator"]()
        self.discriminator = self.type["discriminator"]()
        
        self.text_emb_model = self.type["text_emb_model"]()
        self.text_max_len = self.type["text_max_len"]
        self.use_one_caption = self.type["use_one_caption"]
        self.use_CLS_emb = self.type["use_CLS_emb"]
        # self.text_emb_size = self.type["text_emb_size"] #TODO

        self.g_optim = self.type["g_optim"](self.generator.parameters(), lr=self.type["glr"], betas=(0.5, 0.99))
        self.d_optim = self.type["d_optim"](self.discriminator.parameters(), lr=self.type["dlr"], betas=(0.5, 0.99))
        self.loss = self.type["loss"]
        self.epochs = self.type["epochs"]
        self.cuda = True if torch.cuda.is_available() else False
        self.real_label = 0.9
        self.fake_label = 0.1
        self.samples = 16
        torch.backends.cudnn.benchmark = True

    def run(self, logging_frequency=4):
        """
        This function runs the experiment
        :param logging_frequency: how frequently to log each epoch (default 4)
        :type logging_frequency: int
        :return: None
        :rtype: None
        """

        start_time = time.time()

        explanationSwitch = (self.epochs + 1) / 2 if self.epochs % 2 == 1 else self.epochs / 2

        logger = Logger(self.name, self.type["dataset"])

        
        
        test_noise = noise_coco(self.samples, self.cuda)
        self.generator.apply(weights_init)
        self.discriminator.apply(weights_init)
        

        loader = get_loader(self.type["batchSize"], self.type["percentage"], self.type["dataset"])
        num_batches = len(loader)

        if self.cuda:
            self.generator = self.generator.cuda()
            self.discriminator = self.discriminator.cuda()
            self.loss = self.loss.cuda()

        if self.explainable:
            trained_data = Variable(next(iter(loader))[0])
            if self.cuda:
                trained_data = trained_data.cuda()
        else:
            trained_data = None

        # track losses
        G_losses = []
        D_losses = []

        local_explainable = False

        # Start training
        for epoch in range(1, self.epochs + 1):

            if self.explainable and (epoch - 1) == explanationSwitch:
                

                if self.type["dataset"] == "mscoco":
                    self.generator.out.register_backward_hook(explanation_hook_coco)

                local_explainable = True
            
            #print(loader)

            for n_batch, (real_batch,(captions,file_name)) in enumerate(loader):

                N = real_batch.size(0)

                # 1. Train Discriminator
                # Generate fake data and detach (so gradients are not calculated for generator)
                
                
                fake_data = self.generator(noise_coco(N, self.cuda)).detach()

                

                if self.cuda:
                    real_batch = real_batch.cuda()
                    fake_data = fake_data.cuda()

                # Train D
                d_error, d_pred_real, d_pred_fake = self._train_discriminator(real_data=real_batch, fake_data=fake_data)

                # 2. Train Generator
                # Generate fake data
                
                
                fake_data = self.generator(noise_coco(N, self.cuda))

                

                if self.cuda:
                    fake_data = fake_data.cuda()

                # Train G
                g_error = self._train_generator(fake_data=fake_data, local_explainable=local_explainable,
                                                trained_data=trained_data)

                # Save Losses for plotting later
                G_losses.append(g_error.item())
                D_losses.append(d_error.item())

                logger.log(d_error, g_error, epoch, n_batch, num_batches)

                # Display status Logs
                if n_batch % (num_batches // logging_frequency) == 0:
                    logger.display_status(
                        epoch, self.epochs, n_batch, num_batches,
                        d_error, g_error, d_pred_real, d_pred_fake
                    )

        logger.save_models(generator=self.generator)
        logger.save_errors(g_loss=G_losses, d_loss=D_losses)
        timeTaken = time.time() - start_time
        test_images = self.generator(test_noise)

        
        
        test_images = vectors_to_images_coco(test_images).cpu().data
        calculate_metrics_coco(path=f'{logger.data_subdir}/generator.pt', numberOfSamples=10000)
       

        logger.log_images(test_images, self.epochs + 1, 0, num_batches)
        logger.save_scores(timeTaken, 0)
        return

    def _train_generator(self, fake_data: torch.Tensor, local_explainable, trained_data=None) -> torch.Tensor:
        """
        This function performs one iteration of training the generator
        :param fake_data: tensor data created by generator
        :return: error of generator on this training step
        """
        N = fake_data.size(0)

        # Reset gradients
        self.g_optim.zero_grad()

        # Sample noise and generate fake data
        prediction = self.discriminator(fake_data).view(-1)

        if local_explainable:
            get_explanation(generated_data=fake_data, discriminator=self.discriminator, prediction=prediction,
                            XAItype=self.explanationType, cuda=self.cuda, trained_data=trained_data,
                            data_type=self.type["dataset"])

        # Calculate error and back-propagate
        error = self.loss(prediction, values_target(size=(N,), value=self.real_label, cuda=self.cuda))

        error.backward()

        # clip gradients to avoid exploding gradient problem
        nn.utils.clip_grad_norm_(self.generator.parameters(), 10)

        # update parameters
        self.g_optim.step()

        # Return error
        return error

    def _train_discriminator(self, real_data: Variable, fake_data: torch.Tensor):
        """
        This function performs one iteration of training the discriminator
        :param real_data: batch from dataset
        :type real_data: torch.Tensor
        :param fake_data: data from generator
        :type fake_data: torch.Tensor
        :return: tuple of (mean error, predictions on real data, predictions on generated data)
        :rtype: (torch.Tensor, torch.Tensor, torch.Tensor)
        """
        N = real_data.size(0)
        real_data = real_data.float()

        # Reset gradients
        self.d_optim.zero_grad()

        # 1.1 Train on Real Data
        prediction_real = self.discriminator(real_data).view(-1)

        # Calculate error
        error_real = self.loss(prediction_real, values_target(size=(N,), value=self.real_label, cuda=self.cuda))

        # 1.2 Train on Fake Data
        prediction_fake = self.discriminator(fake_data).view(-1)

        # Calculate error
        error_fake = self.loss(prediction_fake, values_target(size=(N,), value=self.fake_label, cuda=self.cuda))

        # Sum up error and backpropagate
        error = error_real + error_fake
        error.backward()

        # 1.3 Update weights with gradients
        self.d_optim.step()

        # Return error and predictions for real and fake inputs
        return (error_real + error_fake) / 2, prediction_real, prediction_fake
