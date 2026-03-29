import os
import json
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from tqdm import tqdm
import config
from utils.logger import setup_logger

logger = setup_logger("train_scene_classifier")

ALLOWED_LABELS = [
    "testimonial",
    "presenter",
    "b-roll",
    "audience_reaction",
    "establishing_shot",
    "screen_recording",
    "text_slide",
    "other",
]
LABEL_TO_IDX = {k: i for i, k in enumerate(ALLOWED_LABELS)}
IDX_TO_LABEL = {i: k for k, i in LABEL_TO_IDX.items()}

class SceneDataset(Dataset):
    def __init__(self, annotations_file, base_dir, split='train', transform=None):
        self.base_dir = base_dir
        self.transform = transform
        self.samples = []
        
        with open(annotations_file, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                if record["split"] == split:
                    label_idx = LABEL_TO_IDX[record["label"]]
                    for frame_path in record.get("frames", []):
                        if frame_path:
                            self.samples.append({
                                "image_path": os.path.join(self.base_dir, frame_path),
                                "label": label_idx
                            })
                            
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        sample = self.samples[idx]
        image_path = sample["image_path"]
        label = sample["label"]
        
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            # Fallback to empty image if not found (should be rare if exported correctly)
            image = Image.new("RGB", (224, 224))
            
        if self.transform:
            image = self.transform(image)
            
        return image, label

def train_model(data_dir="datasets/scene_type/v1", epochs=10, batch_size=32, lr=1e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    annotations_file = os.path.join(config.BASE_DIR, data_dir, "annotations.jsonl")
    
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    train_dataset = SceneDataset(annotations_file, str(config.BASE_DIR), split='train', transform=train_transform)
    val_dataset = SceneDataset(annotations_file, str(config.BASE_DIR), split='val', transform=val_transform)
    
    logger.info(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    if len(train_dataset) == 0:
        logger.error("No training samples found. Run export_dataset.py first.")
        return
        
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    model = models.resnet18(pretrained=True)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(ALLOWED_LABELS))
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    best_acc = 0.0
    models_dir = os.path.join(config.BASE_DIR, "pipeline", "models")
    os.makedirs(models_dir, exist_ok=True)
    best_model_path = os.path.join(models_dir, "scene_classifier.pth")
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]"):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        train_acc = 100 * correct / (total + 1e-9)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]"):
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
        val_acc = 100 * val_correct / (val_total + 1e-9)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {running_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}% | Val Loss: {val_loss/(len(val_loader)+1e-9):.4f}, Val Acc: {val_acc:.2f}%")
        
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_model_path)
            logger.info(f"Saved best model with Val Acc: {best_acc:.2f}%")
            
    # Save label encoder
    encoder_path = os.path.join(models_dir, "label_encoder.json")
    with open(encoder_path, "w") as f:
        json.dump(IDX_TO_LABEL, f)
        
    logger.info(f"Training complete. Best model saved to {best_model_path}")

if __name__ == "__main__":
    train_model(epochs=5, batch_size=16)
