import unittest
import torch
import tempfile
import os
from n_dock.pre_training import pre_train

class TestPreTraining(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate ImageNet data
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, 'train'))
        
        # Create dummy class directories and images
        for i in range(10):  # Create 10 classes
            class_dir = os.path.join(self.test_dir, 'train', f'n{i:08d}')
            os.makedirs(class_dir)
            for j in range(5):  # Create 5 images per class
                img_path = os.path.join(class_dir, f'img_{j}.jpg')
                with open(img_path, 'w') as f:
                    f.write('dummy image data')

    def tearDown(self):
        # Remove the temporary directory after the test
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_pre_training(self):
        config = {
            'data_path': self.test_dir,
            'epochs': 1,
            'batch_size': 2,
            'in_channels': 3,
            'base_filters': 16,
            'n_blocks': 2,
            'learning_rate': 0.001
        }
        
        model = pre_train(config)
        
        # Check if the model is an instance of SimpleCNN
        self.assertIsInstance(model, torch.nn.Module)
        
        # Check if the model has learned parameters
        for param in model.parameters():
            self.assertIsNotNone(param.grad)
            self.assertNotEqual(torch.sum(param.data), 0)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
import torch
from torch.utils.data import Dataset
from n_dock.pre_training import pre_train

class MockDataset(Dataset):
    def __init__(self, size=100):
        self.size = size

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        return {
            'image': torch.randn(3, 224, 224),
            'label': torch.randint(0, 10, (1,)).item()
        }

class TestPreTraining(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'batch_size': 32,
            'in_channels': 3,
            'base_filters': 16,
            'n_blocks': 4,
            'learning_rate': 0.001,
            'epochs': 2
        }

    @patch('n_dock.pre_training.data_ingest')
    def test_pre_train(self, mock_data_ingest):
        # Mock the data_ingest function
        mock_dataset = MockDataset()
        mock_data_ingest.return_value = mock_dataset

        # Update mock_config to match new API
        self.mock_config['architecture'] = 'SimpleCNN'
        self.mock_config['modality'] = 'image'
        self.mock_config['data_path'] = './data'

        # Run pre_train
        model, get_embedding = pre_train(self.mock_config)

        # What is the type of the model?
        #print(type(model))

        # Assert that data_ingest was called with the correct config
        expected_data_config = {
            'data_type': 'image',
            'data_path': './data',
            'image_size': 224
        }
        mock_data_ingest.assert_called_once_with(expected_data_config)

        # Assert that the model is an instance of SimpleCNN
        self.assertIsInstance(model, torch.nn.Module)

        # Assert that the model has the correct number of parameters
        expected_params = sum(p.numel() for p in model.parameters())
        self.assertGreater(expected_params, 0)

        # Test get_embedding function
        self.assertTrue(callable(get_embedding), "get_embedding should be a callable function")
        
        # Create a dummy input
        dummy_input = torch.randn(1, 3, 224, 224)
        
        # Move the input to the same device as the model
        device = next(model.parameters()).device
        dummy_input = dummy_input.to(device)
        
        # Get embedding using the mocked function
        embedding = get_embedding(dummy_input, model)
        
        # Check if embedding is a tensor
        self.assertIsInstance(embedding, torch.Tensor, "Embedding should be a torch.Tensor")
        
        # Check if embedding has the expected shape
        expected_embedding_size = 256
        self.assertEqual(embedding.shape, (1, expected_embedding_size), f"Embedding shape should be (1, {expected_embedding_size})")
        
        # Move the embedding back to CPU for comparison (if needed)
        embedding = embedding.cpu()

if __name__ == '__main__':
    unittest.main()
