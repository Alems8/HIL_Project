cmake_minimum_required(VERSION 3.26)

project(optitrack)

IF (WIN32)
	link_libraries(ws2_32)
ENDIF()

add_executable(cameras cameras.c)

add_executable(optitrack optitrack_sc.c)