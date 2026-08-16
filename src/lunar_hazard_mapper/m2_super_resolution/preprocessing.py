import numpy as np

def min_max_standardization(imgarr: np.ndarray) -> np.ndarray:
    """
    Apply min-max standardization exactly as performed in the original
    IIT Patna training pipeline to scale pixel values between 0 and 1.
    
    Args:
        imgarr (np.ndarray): 2D array of the low resolution image.
        
    Returns:
        np.ndarray: Normalized 2D array (float32).
    """
    imgarr = imgarr.astype(np.float32)
    min_val = np.min(imgarr)
    max_val = np.max(imgarr)
    if max_val > min_val:
        imgarr = (imgarr - min_val) / (max_val - min_val)
    return imgarr

def denormalize(imgarr: np.ndarray) -> np.ndarray:
    """
    Scale back a [0, 1] standardized tensor/array to [0, 255] for saving.
    """
    imgarr = np.clip(imgarr * 255.0, 0, 255)
    return imgarr.astype(np.uint8)
