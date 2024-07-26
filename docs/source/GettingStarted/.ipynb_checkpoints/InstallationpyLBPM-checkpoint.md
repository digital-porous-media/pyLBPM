## Installing pyLBPM
*Note: Installation should take 3 hours or less

Open your preferred command prompt 

```
mkdir pyLBPM
module load gcc/9.4.0
module load cuda 11.4 
```
To install pyLBPM with pip (note python installs scripts to `$HOME/.local/.bin`)

```
git clone git@github.com:digital-porous-media/pyLBPM.git
cd pyLBPM
pip install ./
export PATH=$HOME/.local/bin:$PATH
```