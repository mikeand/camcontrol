cmake_minimum_required(VERSION 3.4)
project(gpio_pir)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

set(SOURCE_FILES gpio_pir.cpp)
add_executable(gpio_pir ${SOURCE_FILES})

target_link_libraries(gpio_pir wiringPi)
