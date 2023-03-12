# xai-praktikum
TUM WiSe 22/23 - Explainable AI Praktikum Repository
Trains and explains GAN models using various explainability techniques like Saliency, Integrated gradients, LIME, SHAP.
Also, we use explanations to improved GAN's performance.

![Poster](https://github.com/yehiahesham/xai-praktikum/blob/xai-dev/XAI_GAN_Poster.png)


# CONDA 
## Create Env and Install Libs via CONDA :

```
conda create --name XAI_GAN python=3.8
conda activate XAI_GAN
```
Pytorch-CPU:
`conda install -c pytorch pytorch torchvision torchaudio cpuonly `

Pytorch-GPU[Cuda11.7]:
`conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia`

Pytorch-GPU[Cuda11.6]:
`conda install pytorch torchvision torchaudio pytorch-cuda=11.6 -c pytorch -c nvidia`

```
conda install -c pytorch captum -y
conda install -c conda-forge pycocotools opencv -y 
conda install transformers tensorboardX pandas -y
```

Create the environment from the environment.yml file: 

`conda env create -f environment.yml`

Update environment from the environment.yml file: 

`conda env update -n my_env --file ENV.yaml`


# PIP
## Create Env and Install Libs via PIP :

```
python3 -m venv XAI_GAN
source XAI_GAN/bin/activate
pip3 install torch torchvision torchaudio
pip install transformers tensorboardX pandas pycocotools captum  opencv-python
```

# Using Colab and Github

1. create a Github folder in your drive
2. Create a GitHub Personal access token 

  login to your account> Go to Settings> Developer settings>Click on Personal access tokens (classic)> Check the repo checkmark  
  
  Copy Personal access tokens [Don't share it]
  
3. Using  colab terminal, set an env varaibled with your Personal access token  `export GIT_TOKEN=<Personal access>`
4. Clone the repo via `git clone https://$GIT_TOKEN@github.com/theVirus94/xai-praktikum`

## Create a new Enviroment 
1. Create a folder in your drive to host all your virtual enviroments Ex `mkdir /content/drive/MyDrive/YehiaEnv`
2. Create a new env <Env_name> in  envs folder by command `cd /content/drive/MyDrive/YehiaEnv && virtualenv XAI_1` 
3. Activate this env run `source /content/drive/MyDrive/YehiaEnv/XAI_1/bin/activate`

 #  Run the project : 
``` python main.py ``` 
 

