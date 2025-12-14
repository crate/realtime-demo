#!/bin/sh

# Use GCC10 to avoid weird compile issues
export CC=gcc10-gcc
export CXX=gcc10-g++

# Build toolchain for Python 3.13
yum groupinstall -y "Development Tools"
# Use OpenSSL 1.1 for modern Python builds
yum erase -y openssl-devel || true
yum install -y openssl11 openssl11-devel libffi-devel bzip2-devel zlib-devel curl-devel

# EPEL + science libs for netCDF4/h5py
amazon-linux-extras install epel -y

# Build and install Python 3.13 from source
cd /usr/src
wget https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz
tar -xf Python-3.13.1.tgz
cd Python-3.13.1

./configure \
--prefix=/usr/local \
--enable-shared \
LDFLAGS="-Wl,-rpath /usr/local/lib"

make -j"$(nproc)"
make install

# Sanity check
/usr/local/bin/python3.13 --version || python3.13 --version

# Build modern HDFS
cd /usr/src
curl -LO https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.14/hdf5-1.14.3/src/hdf5-1.14.3.tar.gz
tar xf hdf5-1.14.3.tar.gz
cd hdf5-1.14.3

./configure \
    --prefix=/opt/netcdf \
    --with-szlib=/opt/netcdf \
    --enable-hl \
    --enable-threadsafe=no \
    --enable-shared

make -j"$(nproc)"
sudo make install

# Build modern netCDF4
cd /usr/src
curl -LO https://downloads.unidata.ucar.edu/netcdf-c/4.9.2/netcdf-c-4.9.2.tar.gz
tar xf netcdf-c-4.9.2.tar.gz
cd netcdf-c-4.9.2

export CPPFLAGS="-I/opt/netcdf/include"
export LDFLAGS="-L/opt/netcdf/lib"
export LD_LIBRARY_PATH="/opt/netcdf/lib:${LD_LIBRARY_PATH}"

./configure \
    --prefix=/opt/netcdf \
    --enable-netcdf-4 \
    --enable-dap \
    --enable-shared \
    --disable-static

make -j"$(nproc)"
sudo make install

export HDF5_DIR=/opt/netcdf
export NETCDF4_DIR=/opt/netcdf

# Create a Python3.13 venv
cd /home/ec2-user/realtime-demo/data
/usr/local/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip3 install -U -r requirements.txt

# Install Grafana
sudo tee /etc/yum.repos.d/grafana.repo <<EOF
[grafana]
name=Grafana OSS
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
EOF
sudo yum install grafana -y

# Enable and start the service
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
