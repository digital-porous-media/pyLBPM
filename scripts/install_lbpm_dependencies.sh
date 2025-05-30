#!/bin/bash

export GCC_VERSION="9.5.0"
export MPI_VERSION="3.1.2"
export HDF5_VERSION="1.14.3"

# by default don't do these things
INSTALL=NO
DOWNLOAD=NO
INSTALL_DEP_PATH=$HOME/local

for i in "$@"; do
  case $i in
    -i=*|--path=*)
      INSTALL_DEP_PATH="${i#*=}"
      shift # past argument=value
      ;;
    -s=*|--source=*)
      SOURCES="${i#*=}"
      shift # past argument=value
      ;;
    -n=*|--cuda=*)
      CUDADIR="${i#*=}"
      shift # past argument=value
      ;;
    --download)
      DOWNLOAD=YES
      shift # past argument with no value
      ;;
    --install)
      INSTALL=YES
      shift # past argument with no value
      ;;
    -*|--*)
      echo "Unknown option $i"
      exit 1
      ;;
    *)
      ;;
  esac
done


echo "DOWNLOAD=$DOWNLOAD"
echo "INSTALL=$INSTALL"

[[ -z "${INSTALL_DEP_PATH}" ]] && DESTDIR=$HOME/local || DESTDIR="${INSTALL_DEP_PATH}"
[[ -z "${SOURCES}" ]] && SRCDIR=$HOME/.pyLBPM/src || SRCDIR="${SOURCES}"

echo "Installing LBPM dependencies to " $INSTALL_DEP_PATH
echo "Sources path: " $SRCDIR
mkdir -p $SRCDIR
cd $SRCDIR

# Find GCC 9.x
GCC_MODULE=$(module avail 2>&1 | grep -Eo 'gcc/9\.[0-9.]+' | sort -V | tail -1)

if [[ -n "$GCC_MODULE" ]]; then
    echo "GCC Module found: $GCC_MODULE"
    module load $GCC_MODULE
    export GCC_DIR=$(dirname $(dirname $(which gcc)))
    export CC=$(which gcc)
    export CXX=$(which g++)
    echo "Using system GCC: $($CC --version | head -1)"
    BUILD_GCC=false
    GCC_VERSION=$(gcc --version | head -n1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')
else
    echo "No GCC 9.x module found - will build GCC $GCC_VERSION from source"
    BUILD_GCC=true
fi

if [[ "$BUILD_GCC" == true ]]; then
    export GCCSRC="gcc-$GCC_VERSION.tar.gz"
    if [ -f "$GCCSRC" ]; then
	echo "$GCCSRC already downloaded"
    else
	if [[ $DOWNLOAD == YES ]]; then
	    GCC_LINK="https://ftp.gnu.org/gnu/gcc/gcc-$GCC_VERSION/gcc-$GCC_VERSION.tar.gz"
	    echo "$GCCSRC not present, downloading files from $GCC_LINK..."
	    wget $GCC_LINK
	    echo "       ...done"
	else
	    echo "$GCCSRC is not found! exiting"
	    exit;
	fi
    fi
fi  

#export MPISRC="openmpi-4.1.6.tar.gz"
export MPISRC="openmpi-$MPI_VERSION.tar.gz"
if [ -f "$MPISRC" ]; then
    echo "$MPISRC already downloaded"
else
    if [[ $DOWNLOAD == YES ]]; then 
	echo "$MPISRC not present, downloading files..."
	MPI_LINK="https://download.open-mpi.org/release/open-mpi/v3.1/openmpi-$MPI_VERSION.tar.gz"
	echo "$MPISRC not present, downloading files from $MPI_LINK..."
        wget $MPI_LINK
	#wget https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.6.tar.gz
	echo "       ...done"
    else
	echo "$MPISRC is not found! exiting"
	exit;
    fi
fi

#export ZLIBSRC=zlib-1.3.tar.gz
#if [ -f "$ZLIBSRC" ]; then
#    echo "$ZLIBSRC code already downloaded"
#else
#    if [[ $DOWNLOAD == YES ]]; then 
#    echo "$ZLIBSRC not present, downloading files..."
#    wget https://www.zlib.net/zlib-1.3.tar.gz
#    else#
#	echo "$ZLIBSRC is not found! exiting"
#	exit;
#    fi
#fi

export SZIPSRC=szip-2.1.1.tar.gz
if [ -f "$SZIPSRC" ]; then
    echo "$SZIPSRC code already downloaded"
else
    if [[ $DOWNLOAD == YES ]]; then 
        echo "$SZIPSRC not present, downloading files..."
        wget https://support.hdfgroup.org/ftp/lib-external/szip/2.1.1/src/szip-2.1.1.tar.gz
    else
	echo "$SZIPSRC is not found! exiting"
	exit;
    fi
fi

export HDFSRC="hdf5-1.14.3.tar.gz"
if [ -f "$HDFSRC" ]; then
    echo "$HDFSRC code already downloaded"
else
    if [[ $DOWNLOAD == YES ]]; then 
        echo "$HDFSRC not present, downloading files..."
        wget https://hdf-wordpress-1.s3.amazonaws.com/wp-content/uploads/manual/HDF5/HDF5_1_14_3/src/hdf5-1.14.3.tar.gz
    else
	echo "$HDFSRC is not found! exiting"
	exit;
    fi
fi


ls $SRCDIR

#export GCC_DIR=$DESTDIR/gcc/$GCC_VERSION
export MPI_DIR=$DESTDIR/openmpi/$MPI_VERSION
export LBPM_HDF5_DIR=$DESTDIR/hdf5/$HDF5_VERSION
export PATH=$MPI_DIR/bin:$PATH
export LD_LIBRARY_PATH=$MPI_DIR/lib:$LBPM_HDF5_DIR/lib:$LD_LIBRARY_PATH
export LBPM_ZLIB_DIR=$DESTDIR/zlib/1.3
export LBPM_SZIP_DIR=$DESTDIR/szip/

#mkdir -p $GCC_DIR
mkdir -p $MPI_DIR
mkdir -p $LBPM_HDF5_DIR
mkdir -p $LBPM_ZLIB_DIR
mkdir -p $LBPM_SZIP_DIR

#export mode=0
#if [ $mode == 1 ]; then

cd $SRCDIR

# Build and Install GCC 9.x
if [[ $INSTALL == NO || $INSTALL == No || $INSTALL == no ]]; then
    BUILD_GCC=false
fi
# Check if GCC is already installed in the file location
if [ -x $DESTDIR/gcc/$GCC_VERSION/bin/gcc ]; then
  echo "GCC has already been installed... skipping."
  BUILD_GCC=false
  export PATH=$DESTDIR/gcc/$GCC_VERSION/bin:$PATH
fi

if [[ ${BUILD_GCC} == true ]]; then
    export GCC_DIR=$DESTDIR/gcc/$GCC_VERSION
    mkdir -p $GCC_DIR
    echo "Install GCC $GCC_VERSION to $GCC_DIR"
    echo "Extracting tar file..."
    total_files=$(tar -tzf gcc-$GCC_VERSION.tar.gz | wc -l)
    tar --use-compress-program=pigz -xf gcc-$GCC_VERSION.tar.gz --checkpoint=1000 --checkpoint-action='.'
    echo -e "\nExtraction complete!"
    cd gcc-$GCC_VERSION

    # Download GCC dependencies
    echo "Downloading GCC prerequisites"
    ./contrib/download_prerequisites
    echo "Configuring GCC $GCC_VERSION"
    $SRCDIR/gcc-$GCC_VERSION/configure --prefix="$GCC_DIR" --enable-languages=c,c++ --disable-multilib --disable-bootstrap --enable-lto 

    echo "Building GCC (this may take a while)..."
    make -j$(nproc) && make install
else
    export GCC_DIR=$(dirname $(dirname $(which gcc)))
fi
cd $SRCDIR

#try to auto-detect cuda
NVCC=$(which nvcc)
echo "CUDA compiler is found at: $NVCC"
if [[ -f "${NVCC}" ]]; then
    CUDADIR=$(echo $NVCC | sed 's|/bin/nvcc||g')
    echo "Found cuda installation at $CUDADIR"
    echo "Check if a supported GPU is available..."
    GPU_NAME=$(nvidia-smi --query-gpu=gpu_name --format=csv,noheader | tail -1)
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader)
    echo "Found $GPU_COUNT $GPU_NAME"
    if [[ $GPU_NAME == *"A100"* || $GPU_NAME == *"GH200"*  ]]; then
        echo "  ... GPU version is supported will build with cuda support"
    else
        echo "  ... no supported NVIDIA GPU are found."
        unset CUDADIR
        NVCC="no"
    fi
fi

#######################################
# configure openmpi
export BUILD_MPI=true

# check for open mpi
export MPICC=`which mpicc`
export OMPI_INFO=`which ompi_info`
if [[ -n "$OMPI_INFO" ]]; then
    export OMPI_VERSION=$($OMPI_INFO --version | head -1)
fi

if [[ -n "$OMPI_VERSION" && ${OMPI_VERSION} == "Open MPI v$MPI_VERSION" ]]; then
    export MPI_DIR=$(echo $OMPI_INFO | sed 's|/bin/ompi_info||g')
    export BUILD_MPI=false
    echo "Located existing Open MPI. Trying the version installed at $MPI_DIR"
fi

if [[ $INSTALL == NO || $INSTALL == No || $INSTALL == no ]]; then
    BUILD_MPI=false
fi

if [ -x $DESTDIR/openmpi/$MPI_VERSION/bin/mpicc ]; then
    echo "OpenMPI has already been installed. Skipping..."
    BUILD_MPI=false
fi

if [[ ${BUILD_MPI} == true ]]; then
   echo "Install MPI to $MPI_DIR"
   tar -xzvf $MPISRC
   cd openmpi-$MPI_VERSION

   if [[ -f "${CUDADIR}/bin/nvcc" ]]; then
       echo "Building openmpi with cuda support"
       NVCC=${CUDADIR}/bin/nvcc
       echo "CUDA compiler location: $NVCC"
       ./configure --with-cc=${GCC_DIR}/bin/gcc --with-cxx=${GCC_DIR}/bin/g++ --with-fc=${GCC_DIR}/bin/gfortran --with-cuda=${CUDADIR} --enable-mpi-thread-multiple --prefix=${MPI_DIR}
   else
   	echo "Building openmpi without GPU support"
   	./configure --enable-mpi-thread-multiple --prefix=$MPI_DIR
   fi
   # build & install openmpi
   make && make install
   cd $SRCDIR
fi


#######################################

#######################################

export BUILD_HDF5=true
if [[ -f "${LBPM_HDF5_DIR}/bin/h5pcc" ]]; then
    HDF5_COMPILER=$(${LBPM_HDF5_DIR}/bin/h5pcc -showconfig | grep Compiler | awk '{print $3}')
    echo "HDF5 compiler was $HDF5_COMPILER"
    if [[ ${HDF5_COMPILER} == ${MPICC} ]]; then
	echo "Compatible HDF5 build located -- if you really want to rebuild erase the previous installation: $LBPM_HDF5_DIR"
	export BUILD_HDF5=false
    fi
fi

if [[ $INSTALL == NO || $INSTALL == No || $INSTALL == no ]]; then
    BUILD_HDF5=false
fi

# build hdf5
if [[ ${BUILD_HDF5} == true ]]; then
    echo "Install HDF5 to $LBPM_HDF5_DIR"

    # build szip
    tar -xzvf $SZIPSRC
    cd szip-2.1.1
    CC=$MPI_DIR/bin/mpicc CXX=$MPI_DIR/bin/mpicxx CXXFLAGS="-fPIC -O3 -std=c++14" ./configure --prefix=$LBPM_SZIP_DIR && make && make install
    ./libtool --finish $LBPM_SZIP_DIR/lib
    cd $SRCDIR
    
    #build zlib
    #tar -xzvf $ZLIBSRC
    #cd zlib-1.3
    #CC=$MPI_DIR/bin/mpicc CXX=$MPI_DIR/bin/mpicxx CXXFLAGS="-fPIC -O3 -std=c++14" ./configure --prefix=$LBPM_ZLIB_DIR && make && make install
    #cd $SRCDIR

   tar -xzvf $HDFSRC
   cd hdf5-1.14.3
   CC=$MPI_DIR/bin/mpicc CXX=$MPI_DIR/bin/mpicxx CXXFLAGS="-fPIC -O3 -std=c++14" ./configure --prefix=$LBPM_HDF5_DIR --enable-parallel --enable-shared --with-szip=$LBPM_SZIP_DIR
   make -j8 && make install
   cd $SRCIR
   #--with-zlib=$LBPM_ZLIB_DIR 
fi

#######################################
export LBPM_CONFIG_DIR=$HOME/.pyLBPM
mkdir -p ${LBPM_CONFIG_DIR}
echo '#!/bin/bash' > $LBPM_CONFIG_DIR/config.sh
echo "export MPI_VERSION=$MPI_VERSION" >> $LBPM_CONFIG_DIR/config.sh
echo "export HDF5_VERSION=$HDF5_VERSION" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_CONFIG_DIR=$HOME/.pyLBPM" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_GIT_REPO=https://github.com/OPM/LBPM.git" >> $LBPM_CONFIG_DIR/config.sh
echo "export SOURCE_DIR=$SRCDIR" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_INSTALL_ROOT_DIR=$INSTALL_DEP_PATH" >> $LBPM_CONFIG_DIR/config.sh
if [[ -f $NVCC ]]; then
    echo 'export mode="nvidia"' >> $LBPM_CONFIG_DIR/config.sh
    echo "export NVCC=$NVCC" >> $LBPM_CONFIG_DIR/config.sh
else
    echo 'export mode="cpu"' >> $LBPM_CONFIG_DIR/config.sh
fi
echo "export GCC9=$GCC_DIR" >> $LBPM_CONFIG_DIR/config.sh
echo "export MPICC=$MPI_DIR/bin/mpicc"  >> $LBPM_CONFIG_DIR/config.sh
echo "export MPICXX=$MPI_DIR/bin/mpicxx"  >> $LBPM_CONFIG_DIR/config.sh
echo "export MPI_DIR=$MPI_DIR"  >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_HDF5_DIR=$LBPM_HDF5_DIR"  >> $LBPM_CONFIG_DIR/config.sh
echo "export LD_LIBRARY_PATH=$GCC_DIR/lib64:$MPI_DIR/lib:$LBPM_HDF5_DIR/lib:$LD_LIBRARY_PATH" >> $LBPM_CONFIG_DIR/config.sh
echo "export PATH=$GCC_DIR/bin:$PATH" >> $LBPM_CONFIG_DIR/config.sh
echo "export PATH=$MPI_DIR/bin:$PATH" >> $LBPM_CONFIG_DIR/config.sh

exit;

