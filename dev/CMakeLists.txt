cmake_minimum_required(VERSION 3.20)
project(wangcai_orderbook_cpp LANGUAGES CXX)

# 查找依赖
find_package(Boost CONFIG REQUIRED)

# 查找pybind11 - 支持多种安装方式
find_package(pybind11 REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if (CMAKE_BUILD_TYPE STREQUAL "Release")
    message(STATUS "Speed-optimized build (Release) enabled")
    add_compile_options(
        -O3
        -march=native
        -flto
        -DNDEBUG
        -fno-rtti
        -ffast-math

    )
    add_link_options(-flto)
endif()

# 基础库源文件
set(LIB_SOURCES
    src/orderbook.cpp
    src/call_auction_engine.cpp
    src/con_auction_engine.cpp
    src/OrderLoader.cpp
    src/close_auction_engine.cpp
    src/orderdb.cpp
    src/backtest_engine.cpp
)

# 基础库
add_library(wangcai_orderbook_cpp STATIC ${LIB_SOURCES})
target_include_directories(wangcai_orderbook_cpp PUBLIC include ${Boost_INCLUDE_DIRS})
target_link_libraries(wangcai_orderbook_cpp PRIVATE Boost::boost)

# Python 绑定模块
pybind11_add_module(pywangcai_orderbook 
    src/python_bindings.cpp  # 我们需要创建这个文件
    ${LIB_SOURCES}
)

# 配置Python模块
target_include_directories(pywangcai_orderbook PRIVATE include ${Boost_INCLUDE_DIRS})
target_link_libraries(pywangcai_orderbook PRIVATE Boost::boost)

# Python模块编译选项
target_compile_definitions(pywangcai_orderbook PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# 回测程序（包含回测引擎）
add_executable(backtest_main 
    src/backtest_main.cpp
)
add_executable(SnapshotDB_main 
    src/snapshotdb_main.cpp
)

add_executable(SnapshotDB_test 
    test/snapshotdb_acuracy_test.cpp
)

target_link_libraries(backtest_main PRIVATE wangcai_orderbook_cpp Boost::boost)
target_include_directories(backtest_main PRIVATE include ${Boost_INCLUDE_DIRS})

target_link_libraries(SnapshotDB_main PRIVATE wangcai_orderbook_cpp Boost::boost)  
target_include_directories(SnapshotDB_main PRIVATE include ${Boost_INCLUDE_DIRS})

target_link_libraries(SnapshotDB_test  PRIVATE wangcai_orderbook_cpp Boost::boost)  
target_include_directories(SnapshotDB_test  PRIVATE include ${Boost_INCLUDE_DIRS})