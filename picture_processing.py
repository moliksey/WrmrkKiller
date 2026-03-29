import torch
from PIL import Image
import numpy as np
from torchvision import transforms

transform = transforms.Compose([transforms.Resize((256, 256)),
                                transforms.ToTensor(),])

def process_large_image(image, model, tile_size=256, overlap=32,  device='cpu'):
    w, h = image.size

    image_np = np.array(image).astype(np.float32) / 255.0
    result = np.zeros_like(image_np)
    weight = np.zeros_like(image_np)

    step = tile_size - overlap

    for y in range(0, h, step):
        for x in range(0, w, step):
            x_end = min(x + tile_size, w)
            y_end = min(y + tile_size, h)

            tile = image_np[y:y_end, x:x_end]

            pad_x = tile_size - tile.shape[1]
            pad_y = tile_size - tile.shape[0]

            if pad_x > 0 or pad_y > 0:
                tile = np.pad(tile, ((0, pad_y), (0, pad_x), (0, 0)), mode='reflect')

            tensor = torch.from_numpy(tile).permute(2,0,1).unsqueeze(0).to(device)

            with torch.no_grad():
                out = model(tensor)

            out = out.squeeze(0).cpu().permute(1,2,0).numpy()
            out = out[:y_end-y, :x_end-x]

            result[y:y_end, x:x_end] += out
            weight[y:y_end, x:x_end] += 1

    result /= weight
    result = np.clip(result,0,1)

    return Image.fromarray((result*255).astype(np.uint8))

def process_test_image(image, model, device='cpu'):
    original_size = image.size  
    input_tensor = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
            output_tensor = model(input_tensor)

    predicted_image = output_tensor.squeeze(0).cpu().permute(1, 2, 0).clamp(0, 1).numpy()
    predicted_pil = Image.fromarray((predicted_image * 255).astype(np.uint8))
    predicted_pil = predicted_pil.resize(original_size, Image.Resampling.LANCZOS)
    return predicted_pil