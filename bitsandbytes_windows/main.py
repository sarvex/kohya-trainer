"""
extract factors the build is dependent on:
[X] compute capability
    [ ] TODO: Q - What if we have multiple GPUs of different makes?
- CUDA version
- Software:
    - CPU-only: only CPU quantization functions (no optimizer, no matrix multiple)
    - CuBLAS-LT: full-build 8-bit optimizer
    - no CuBLAS-LT: no 8-bit matrix multiplication (`nomatmul`)

evaluation:
    - if paths faulty, return meaningful error
    - else:
        - determine CUDA version
        - determine capabilities
        - based on that set the default path
"""

import ctypes

from .paths import determine_cuda_runtime_lib_path


def check_cuda_result(cuda, result_val):
    # 3. Check for CUDA errors
    if result_val != 0:
        error_str = ctypes.c_char_p()
        cuda.cuGetErrorString(result_val, ctypes.byref(error_str))
        print(f"CUDA exception! Error code: {error_str.value.decode()}")

def get_cuda_version(cuda, cudart_path):
    # https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART____VERSION.html#group__CUDART____VERSION
    try:
        cudart = ctypes.CDLL(cudart_path)
    except OSError:
        # TODO: shouldn't we error or at least warn here?
        print(f'ERROR: libcudart.so could not be read from path: {cudart_path}!')
        return None

    version = ctypes.c_int()
    check_cuda_result(cuda, cudart.cudaRuntimeGetVersion(ctypes.byref(version)))
    version = int(version.value)
    major = version//1000
    minor = (version-(major*1000))//10

    if major < 11:
       print('CUDA SETUP: CUDA version lower than 11 are currently not supported for LLM.int8(). You will be only to use 8-bit optimizers and quantization routines!!')

    return f'{major}{minor}'


def get_cuda_lib_handle():
    # 1. find libcuda.so library (GPU driver) (/usr/lib)
    try:
        cuda = ctypes.CDLL("libcuda.so")
    except OSError:
        # TODO: shouldn't we error or at least warn here?
        print('CUDA SETUP: WARNING! libcuda.so not found! Do you have a CUDA driver installed? If you are on a cluster, make sure you are on a CUDA machine!')
        return None
    check_cuda_result(cuda, cuda.cuInit(0))

    return cuda


def get_compute_capabilities(cuda):
    """
    1. find libcuda.so library (GPU driver) (/usr/lib)
       init_device -> init variables -> call function by reference
    2. call extern C function to determine CC
       (https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__DEVICE__DEPRECATED.html)
    3. Check for CUDA errors
       https://stackoverflow.com/questions/14038589/what-is-the-canonical-way-to-check-for-errors-using-the-cuda-runtime-api
    # bits taken from https://gist.github.com/f0k/63a664160d016a491b2cbea15913d549
    """


    nGpus = ctypes.c_int()
    cc_major = ctypes.c_int()
    cc_minor = ctypes.c_int()

    device = ctypes.c_int()

    check_cuda_result(cuda, cuda.cuDeviceGetCount(ctypes.byref(nGpus)))
    ccs = []
    for i in range(nGpus.value):
        check_cuda_result(cuda, cuda.cuDeviceGet(ctypes.byref(device), i))
        ref_major = ctypes.byref(cc_major)
        ref_minor = ctypes.byref(cc_minor)
        # 2. call extern C function to determine CC
        check_cuda_result(
            cuda, cuda.cuDeviceComputeCapability(ref_major, ref_minor, device)
        )
        ccs.append(f"{cc_major.value}.{cc_minor.value}")

    return ccs


# def get_compute_capability()-> Union[List[str, ...], None]: # FIXME: error
def get_compute_capability(cuda):
    """
    Extracts the highest compute capbility from all available GPUs, as compute
    capabilities are downwards compatible. If no GPUs are detected, it returns
    None.
    """
    ccs = get_compute_capabilities(cuda)
    return ccs[-1] if ccs is not None else None


def evaluate_cuda_setup():
    print('')
    print('='*35 + 'BUG REPORT' + '='*35)
    print('Welcome to bitsandbytes. For bug reports, please submit your error trace to: https://github.com/TimDettmers/bitsandbytes/issues')
    print('For effortless bug reporting copy-paste your error into this form: https://docs.google.com/forms/d/e/1FAIpQLScPB8emS3Thkp66nvqwmjTEgxp8Y9ufuWTzFyr9kJ5AoI47dQ/viewform?usp=sf_link')
    print('='*80)
    return "libbitsandbytes_cuda116.dll"            # $$$
