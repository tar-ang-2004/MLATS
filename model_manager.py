"""
Model Manager with Singleton Pattern
Optimizes ML model loading and memory usage
"""

import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton pattern for managing ML models
    Ensures models are loaded once and shared across requests
    """
    
    _instance = None
    _lock = threading.Lock()
    _models = {}
    _model_stats = {}
    
    def __new__(cls):
        """Singleton implementation with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize model manager (called once)"""
        if self._initialized:
            return
            
        logger.info("Initializing Model Manager")
        self._initialized = True
        self._load_models()
    
    def _load_models(self):
        """Load all required models lazily"""
        logger.info("Model Manager ready - models will be loaded on demand")
    
    def get_sentence_transformer(self, model_name: str = 'all-MiniLM-L6-v2') -> Any:
        """
        Get sentence transformer model (loaded once)
        
        Args:
            model_name: Name of the sentence transformer model
            
        Returns:
            Loaded sentence transformer model
        """
        model_key = f"sentence_transformer_{model_name}"
        
        if model_key not in self._models:
            with self._lock:
                if model_key not in self._models:
                    logger.info(f"Loading sentence transformer model: {model_name}")
                    start_time = datetime.now(timezone.utc)
                    
                    try:
                        from sentence_transformers import SentenceTransformer
                        model = SentenceTransformer(model_name)
                        
                        self._models[model_key] = model
                        self._model_stats[model_key] = {
                            'loaded_at': start_time,
                            'load_time': (datetime.now(timezone.utc) - start_time).total_seconds(),
                            'usage_count': 0,
                            'model_name': model_name,
                            'model_type': 'sentence_transformer'
                        }
                        
                        logger.info(f"Sentence transformer model loaded in {self._model_stats[model_key]['load_time']:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"Failed to load sentence transformer model {model_name}: {e}")
                        raise
        
        # Increment usage count
        self._model_stats[model_key]['usage_count'] += 1
        return self._models[model_key]
    
    def get_tfidf_vectorizer(self) -> Any:
        """
        Get TF-IDF vectorizer (loaded once)
        
        Returns:
            Loaded TF-IDF vectorizer
        """
        model_key = "tfidf_vectorizer"
        
        if model_key not in self._models:
            with self._lock:
                if model_key not in self._models:
                    logger.info("Loading TF-IDF vectorizer")
                    start_time = datetime.now(timezone.utc)
                    
                    try:
                        from sklearn.feature_extraction.text import TfidfVectorizer
                        
                        # Configure vectorizer
                        vectorizer = TfidfVectorizer(
                            max_features=5000,
                            stop_words='english',
                            ngram_range=(1, 2),
                            lowercase=True,
                            strip_accents='ascii'
                        )
                        
                        self._models[model_key] = vectorizer
                        self._model_stats[model_key] = {
                            'loaded_at': start_time,
                            'load_time': (datetime.now(timezone.utc) - start_time).total_seconds(),
                            'usage_count': 0,
                            'model_type': 'tfidf_vectorizer'
                        }
                        
                        logger.info(f"TF-IDF vectorizer loaded in {self._model_stats[model_key]['load_time']:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"Failed to load TF-IDF vectorizer: {e}")
                        raise
        
        self._model_stats[model_key]['usage_count'] += 1
        return self._models[model_key]
    
    def get_skill_extractor(self) -> Any:
        """
        Get skill extraction model (loaded once)
        
        Returns:
            Skill extraction model or pattern matcher
        """
        model_key = "skill_extractor"
        
        if model_key not in self._models:
            with self._lock:
                if model_key not in self._models:
                    logger.info("Loading skill extraction model")
                    start_time = datetime.now(timezone.utc)
                    
                    try:
                        # For now, use a simple pattern-based extractor
                        # Can be enhanced with NER models later
                        from ats_components import SkillExtractor
                        extractor = SkillExtractor()
                        
                        self._models[model_key] = extractor
                        self._model_stats[model_key] = {
                            'loaded_at': start_time,
                            'load_time': (datetime.now(timezone.utc) - start_time).total_seconds(),
                            'usage_count': 0,
                            'model_type': 'skill_extractor'
                        }
                        
                        logger.info(f"Skill extractor loaded in {self._model_stats[model_key]['load_time']:.2f}s")
                        
                    except Exception as e:
                        logger.error(f"Failed to load skill extractor: {e}")
                        # Fallback to None if not available
                        self._models[model_key] = None
                        self._model_stats[model_key] = {
                            'loaded_at': start_time,
                            'load_time': 0,
                            'usage_count': 0,
                            'model_type': 'skill_extractor',
                            'error': str(e)
                        }
        
        if self._models[model_key] is not None:
            self._model_stats[model_key]['usage_count'] += 1
        return self._models[model_key]
    
    def preload_models(self):
        """
        Preload all models to avoid lazy loading delays
        Useful for production warmup
        """
        logger.info("Preloading all models...")
        start_time = datetime.now(timezone.utc)
        
        models_to_preload = [
            ('sentence_transformer', lambda: self.get_sentence_transformer()),
            ('tfidf_vectorizer', lambda: self.get_tfidf_vectorizer()),
            ('skill_extractor', lambda: self.get_skill_extractor()),
        ]
        
        loaded_count = 0
        failed_count = 0
        
        for model_name, loader in models_to_preload:
            try:
                loader()
                loaded_count += 1
                logger.info(f"Preloaded {model_name}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to preload {model_name}: {e}")
        
        total_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"Model preloading completed: {loaded_count} loaded, {failed_count} failed, {total_time:.2f}s total")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded models
        
        Returns:
            Dictionary with model statistics
        """
        return {
            'total_models': len(self._models),
            'models': dict(self._model_stats),
            'memory_info': self._get_memory_info()
        }
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def clear_model(self, model_key: str) -> bool:
        """
        Clear a specific model from memory
        
        Args:
            model_key: Key of the model to clear
            
        Returns:
            True if model was cleared, False if not found
        """
        with self._lock:
            if model_key in self._models:
                del self._models[model_key]
                if model_key in self._model_stats:
                    del self._model_stats[model_key]
                logger.info(f"Cleared model: {model_key}")
                return True
            return False
    
    def clear_all_models(self):
        """Clear all models from memory"""
        with self._lock:
            self._models.clear()
            self._model_stats.clear()
            logger.info("Cleared all models from memory")

# Global model manager instance
model_manager = ModelManager()

# Convenience functions
def get_sentence_transformer(model_name: str = 'all-MiniLM-L6-v2'):
    """Get sentence transformer model"""
    return model_manager.get_sentence_transformer(model_name)

def get_tfidf_vectorizer():
    """Get TF-IDF vectorizer"""
    return model_manager.get_tfidf_vectorizer()

def get_skill_extractor():
    """Get skill extraction model"""
    return model_manager.get_skill_extractor()

def preload_all_models():
    """Preload all models for production"""
    return model_manager.preload_models()

def get_model_statistics():
    """Get model usage statistics"""
    return model_manager.get_model_stats()