#!/bin/bash

export SOURCE_DIR=$HOME/.pyLBPM/src

if [[ -z "${LBPM_CONFIG_DIR}" ]]; then
   source ~/.pyLBPM/config.sh
fi

export LBPM_INSTALL_DIR=$LBPM_INSTALL_ROOT_DIR/LBPM
export LBPM_SOURCE_DIR=$SOURCE_DIR/LBPM

echo "Preparing to compile LBPM" 
echo "       mode: $mode"

if [[ $mode == "nvidia" ]]; then
    echo "       GPU COMPILER PATH"
    echo "           NVCC: $NVCC"
fi
echo "       MPI_DIR: $MPI_DIR"
echo "       LBPM_HDF5_DIR: $LBPM_HDF5_DIR"
echo "       LBPM_INSTALL_ROOT_DIR: $LBPM_INSTALL_ROOT_DIR"
echo "       SOURCE_DIR: $SOURCE_DIR"


cd $SOURCE_DIR
if [[ -d $LBPM_SOURCE_DIR ]]; then
    echo "LBPM source code at $LBPM_SOURCE_DIR"
    cd $LBPM_SOURCE_DIR
else
    echo "Download LBPM from Open Porous Media Project..."
    git clone $LBPM_GIT_REPO
    cd $LBPM_SOURCE_DIR
fi
export LBPM_GIT_COMMIT=$(git log -1 | head -1 | awk '{print $2}')
cd $SOURCE_DIR


mkdir -p $LBPM_INSTALL_DIR
cd $LBPM_INSTALL_DIR
echo "Installing LBPM to $LBPM_INSTALL_DIR"

if [[ mode == "nvidia" ]]; then
    echo "Building for $mode mode. Path to cuda compiler is $NVCC"
    export CUDA_HOST_COMPILER=`which gcc`
    rm -rf CMake*
    cmake                                    \
	-D CMAKE_C_COMPILER:PATH=$MPICC          \
	-D CMAKE_CXX_COMPILER:PATH=$MPICXX        \
	-D CMAKE_C_FLAGS="-fPIC"            \
	-D CMAKE_CXX_FLAGS="-fPIC"          \
	-D MPIEXEC=mpirun                     \
	-D USE_EXT_MPI_FOR_SERIAL_TESTS:BOOL=TRUE \
	-D CMAKE_BUILD_TYPE:STRING=Release     \
	-D USE_CUDA=1			   \
           -D CMAKE_CUDA_FLAGS="-arch sm_80 -Xptxas=-v -Xptxas -dlcm=cg -lineinfo" \
           -D CMAKE_CUDA_HOST_COMPILER=$CUDA_HOST_COMPILER \
        -D USE_HDF5=1				   \
           -D HDF5_DIRECTORY="$LBPM_HDF5_DIR"		   \
    	   -D HDF5_LIB="$LBPM_HDF5_DIR/lib/libhdf5.so"	   \
        -D USE_TIMER=0			 \
	 $LBPM_SOURCE_DIR
  
else
    echo "Building for $mode mode. "
    rm -rf CMake*
    cmake                                    \
	-D CMAKE_C_COMPILER:PATH=$MPICC          \
	-D CMAKE_CXX_COMPILER:PATH=$MPICXX        \
	-D CMAKE_C_FLAGS="-fPIC"            \
	-D CMAKE_CXX_FLAGS="-fPIC"          \
	-D MPIEXEC=mpirun                     \
	-D USE_EXT_MPI_FOR_SERIAL_TESTS:BOOL=TRUE \
	-D CMAKE_BUILD_TYPE:STRING=Release     \
	-D USE_CUDA=0			   \
        -D USE_HDF5=1				   \
           -D HDF5_DIRECTORY="$LBPM_HDF5_DIR"		   \
    	   -D HDF5_LIB="$LBPM_HDF5_DIR/lib/libhdf5.so"	   \
        -D USE_TIMER=0			 \
	 $LBPM_SOURCE_DIR
fi

make -j  VERBOSE=1 && make install

mkdir -p ${LBPM_CONFIG_DIR}
echo '#!/bin/bash' > $LBPM_CONFIG_DIR/config.sh
echo "export MPI_VERSION=$MPI_VERSION" >> $LBPM_CONFIG_DIR/config.sh
echo "export HDF5_VERSION=$HDF5_VERSION" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_CONFIG_DIR=$HOME/.pyLBPM" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_GIT_REPO=https://github.com/OPM/LBPM.git" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_GIT_COMMIT=$LBPM_GIT_COMMIT" >> $LBPM_CONFIG_DIR/config.sh
echo "export SOURCE_DIR=$SOURCE_DIR" >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_SOURCE_DIR=$LBPM_SOURCE_DIR" >> $LBPM_CONFIG_DIR/config.sh
echo "export MPI_DIR=$MPI_DIR"  >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_BIN=$LBPM_INSTALL_DIR/bin" >> $LBPM_CONFIG_DIR/config.sh
if [[ -f $NVCC ]]; then
    echo 'export mode="nvidia"' >> $LBPM_CONFIG_DIR/config.sh
    echo "export NVCC=$NVCC" >> $LBPM_CONFIG_DIR/config.sh
else
    echo 'export mode="cpu"' >> $LBPM_CONFIG_DIR/config.sh
fi
echo "export MPICC=$MPI_DIR/bin/mpicc"  >> $LBPM_CONFIG_DIR/config.sh
echo "export MPICXX=$MPI_DIR/bin/mpicxx"  >> $LBPM_CONFIG_DIR/config.sh
echo "export MPI_DIR=$MPI_DIR"  >> $LBPM_CONFIG_DIR/config.sh
echo "export LBPM_HDF5_DIR=$LBPM_HDF5_DIR"  >> $LBPM_CONFIG_DIR/config.sh
echo "export LD_LIBRARY_PATH=$MPI_DIR/lib:$LBPM_HDF5_DIR/lib:$LD_LIBRARY_PATH" >> $LBPM_CONFIG_DIR/config.sh
echo "export PATH=$MPI_DIR/bin:$PATH" >> $LBPM_CONFIG_DIR/config.sh
echo "Config file updated"

exit;
