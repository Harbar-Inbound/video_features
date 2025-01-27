# Multi-GPU Extraction of Video Features

This is a PyTorch module that does a feature extraction in parallel on any number of GPUs. So far, I3D and VGGish features are supported.

## Running with CPU only

This repository contains some changes to accommodate running the dependencies for the BMT repository without the need for
a GPU with 8GB VRAM available (needed for I3D feature extraction). As such, we introduce the `--nocuda` flag, to run everything on the CPU.

### Disclaimer  
Let's first consider the pros and cons of running with the `--nocuda` flag.

**Pros:**

 * Allows to run the feature extraction without the need for a powerful GPU.

**Cons:**
 
 * The implementation introduces a [third party dependency](https://github.com/ClementPinard/Pytorch-Correlation-extension).
 * The used `CrossCorrelationSampler` implementation provides slightly different outputs w.r.t the original
 implementation.
 * The CPU based extraction is not particularly fast. On a Nvidia K80 (Google Collab gpu) a 20 second video is processed
in 20 seconds with I3D, while the CPU counterpart takes roughly 167 seconds on an 18 second video
   
### Getting started

Creating a virtual environment following the commands below should allow your to start extracting features with only the
CPU.

```bash
python -m venv venv
source venv/bin/activate
pip install -r -U cpu_requirements.txt
```

It may be that you need to install the [third party dependency by Clement Pinard](https://github.com/ClementPinard/Pytorch-Correlation-extension)
manually. To do so, run the following commands, or check the [repository](https://github.com/ClementPinard/Pytorch-Correlation-extension)
to see how to install the package.

```bash
git clone https://github.com/ClementPinard/Pytorch-Correlation-extension.git
cd Pytorch-Correlation-extension
python -m setup.py install
```

After that has completed you can run the feature extraction as described below, but with CPU only! Happy hacking!

**I3D** (optical flow)
```bash
python main.py --feature_type i3d --file_with_video_paths ./sample/sample_video_paths.txt --nocuda
```

**VGGish** (audio)
Make sure to setup the PyTorch network as described in the following [Setup the Environment for VGGish \(Pytorch\)](#setup-the-environment-for-vggish-\(pytorch\))
```bash
python main.py --feature_type vggish --file_with_video_paths ./sample/sample_video_paths.txt --nocuda
```

## I3D

Please note, this implementation uses PWC-Net instead of the TVL1 algorithm, which was used in the original I3D paper as PWC Net is much faster. Yet, one may create a Pull Request implementing TVL1 as an option to form optical flow frames.

### Set up the Environment for I3D
Setup `conda` environment. Requirements are in file `conda_env_i3d.yml`
```bash
# it will create new conda environment called 'i3d' on your machine 
conda env create -f conda_env_i3d.yml
conda activate i3d
```

### Examples
It will extract I3D features for sample videos using 0th and 2nd devices in parallel. The features are going to be extracted with the default parameters. Check out `python main.py --help` for help on available options.
```bash
python main.py --feature_type i3d --device_ids 0 2 --video_paths ./sample/v_ZNVhz7ctTq0.mp4 ./sample/v_GGSY1Qvo990.mp4
```

The video paths can be specified as a `.txt` file with paths
```bash
python main.py --feature_type i3d --device_ids 0 2 --file_with_video_paths ./sample/sample_video_paths.txt
```

The features can be saved as numpy arrays by specifying `--on_extraction save_numpy`. By default, it will create a folder `./output` and will store features there
```bash
python main.py --feature_type i3d --device_ids 0 2 --on_extraction save_numpy --file_with_video_paths ./sample/sample_video_paths.txt
```
You can change the output folder using `--output_path` argument.

Also, you may want to try to change I3D window and step sizes
```bash
python main.py --feature_type i3d --device_ids 0 2 --stack_size 24 --step_size 24 --file_with_video_paths ./sample/sample_video_paths.txt
```

By default, the frames are extracted according to the original fps of a video. If you would like to extract frames at a certain fps, specify `--extraction_fps` argument.
```bash
python main.py --feature_type i3d --device_ids 0 2 --extraction_fps 25 --stack_size 24 --step_size 24 --file_with_video_paths ./sample/sample_video_paths.txt
```

If `--keep_frames` is specified, it keeps them in `--tmp_path` which is `./tmp` by default. Be careful with the `--keep_frames` argument when playing with `--extraction_fps` as it may mess up the frames you extracted before in the same folder.

### Credits
1. An implementation of PWC-Net in PyTorch: https://github.com/sniklaus/pytorch-pwc
2. A port of I3D weights from TensorFlow to PyTorch: https://github.com/hassony2/kinetics_i3d_pytorch
3. The I3D paper: [Quo Vadis, Action Recognition? A New Model and the Kinetics Dataset](https://arxiv.org/abs/1705.07750).

### License 
All is MIT except for PWC Net implementation in I3D. Please read the PWC implementation [License](https://github.com/sniklaus/pytorch-pwc) (Last time I checked it was _GPL-3.0_).

## VGGish

The extraction of VGGish features can be extracted either by using a Wrapped version (original) or Pytorch re-implementation
that uses a ported version.

### Setup the Environment for VGGish (Pytorch)
Setup `conda` environment. Requirements are in the file `conda_env_vggish_pytorch.yml`.

```bash
# it will create new conda environment called 'vggish' on your machine 
conda env create -f conda_env_vggish_pytorch.yml
conda activate vggish
```
To download the models, follow the instructions in the submodules [README](https://github.com/Harbar-Inbound/VGGish-pytorch#pre-generated-files),
or generate your own [version](https://github.com/Harbar-Inbound/VGGish-pytorch#generate-from-checkpoint). 

### Example
The only difference during execution w.r.t. the original implementation, is that the `--pytorch` flag must be set, 
otherwise the Tensorflow implementation is used.
```bash
python main.py --pytorch --feature_type vggish --device_ids 0 2 --video_paths ./sample/v_ZNVhz7ctTq0.mp4 ./sample/v_GGSY1Qvo990.mp4 
```
See `python main.py --help` for more arguments and I3D examples

### Set up the Environment for VGGish (Tensorflow)
Setup `conda` environment. Requirements are in file `conda_env_vggish.yml`
```bash
# it will create new conda environment called 'vggish' on your machine 
conda env create -f conda_env_vggish.yml
conda activate vggish
# download the pre-trained VGGish model. The script will put the files in the checkpoint directory
wget https://storage.googleapis.com/audioset/vggish_model.ckpt -P ./models/vggish/checkpoints
```

### Example

```bash
python main.py --feature_type vggish --device_ids 0 2 --video_paths ./sample/v_ZNVhz7ctTq0.mp4 ./sample/v_GGSY1Qvo990.mp4
```
See `python main.py --help` for more arguments and I3D examples

### Credits
1. The [TensorFlow implementation](https://github.com/tensorflow/models/tree/0b3a8abf095cb8866ca74c2e118c1894c0e6f947/research/audioset/vggish). 
2. The VGGish paper: [CNN Architectures for Large-Scale Audio Classification](https://arxiv.org/abs/1609.09430).

### License 
My code (this wrapping) is under MIT but the tf implementation complies with the `tensorflow` license which is [Apache-2.0](https://github.com/tensorflow/models/blob/master/LICENSE).