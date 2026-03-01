from PIL import Image
import numpy as np

def clean_checkered_bg(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    data = np.array(img)
    
    # Checkered pattern is typically neutral greys
    # We remove anything where R ≈ G ≈ B and it's not red-dominant
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Neutrals are where R,G,B are close to each other
    is_neutral = (np.abs(r.astype(int) - g.astype(int)) < 30) & \
                 (np.abs(g.astype(int) - b.astype(int)) < 30) & \
                 (np.abs(r.astype(int) - b.astype(int)) < 30)
                 
    # We also avoid removing the Red Ferrari body (where R is much higher than G and B)
    is_ferrari_red = (r > 120) & (r > (g.astype(int) + 30)) & (r > (b.astype(int) + 30))
    
    # Mask to remove: neutral greys that aren't the red body
    to_remove = is_neutral & (~is_ferrari_red)
    
    data[to_remove, 3] = 0 # Make transparent
    
    Image.fromarray(data).save(out_path)

if __name__ == "__main__":
    clean_checkered_bg("f1_car.png", "f1_car_clean.png")
