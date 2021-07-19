ln -s /usr/lib64/libOpenGL.so.0 /usr/lib64/libOpenGL.so
# ls /usr/lib/
# ls /usr/lib64/
# /opt/python/cp36-cp36m/bin/pip install --no-cache-dir numpy
# /opt/python/cp39-cp39m/bin/pip install --no-cache-dir numpy

python3.6 -m pip install --no-cache-dir numpy
python3.9 -m pip install --no-cache-dir numpy
python3.10 -m pip install --no-cache-dir numpy

# /opt/python/cp36-cp36m/bin/pip show numpy
# ls /usr/local/lib/

# # Install Eigen
# git clone https://gitlab.com/libeigen/eigen.git
# cd eigen
# git checkout 3.3.9
# mkdir build && cd build
# cmake ..
# make -j2
# make install
# cd ../../

# # Install OpenCV
# git clone https://github.com/opencv/opencv.git
# cd opencv
# git checkout 4.5.2
# mkdir build && cd build
# cmake -DWITH_VTK=OFF -DWITH_GTK=OFF -DWITH_PROTOBUF=OFF -DBUILD_PERF_TESTS=OFF -DBUILD_TESTS=OFF -DWITH_WEBP=OFF ..
# make -j2
# make install
# cd ../../

# # Install PyBind11
# git clone https://github.com/pybind/pybind11.git
# cd pybind11
# git checkout v2.6.2
# mkdir build && cd build
# cmake -DPYBIND11_TEST=OFF ..
# make -j2
# make install
# cd ../../
