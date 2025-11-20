"""Test module for Papago enhanced translation functionality"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.translation import (
    validate_language_codes,
    split_text_semantically,
    translate_with_retry,
    translate_batch_enhanced,
    translate_structure_enhanced,
    translate_chunk_analysis_enhanced,
    get_translation_supported_languages,
    SUPPORTED_LANGUAGES
)


class TestPapagoEnhanced(unittest.TestCase):
    """Test cases for Papago enhanced translation module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_client_id = "test_client_id"
        self.valid_client_secret = "test_client_secret"
        self.sample_texts = [
            "안녕하세요. 반갑습니다.",
            "테스트 문장입니다.",
            "파이썬 프로그래밍 언어"
        ]
        
        self.sample_structure = {
            "name": "테스트 구조",
            "synthesis": "이것은 테스트 구조입니다.",
            "categories": [
                {
                    "name": "카테고리 1",
                    "concepts": [
                        {
                            "name": "개념 1",
                            "subconcepts": [
                                {
                                    "name": "하위 개념 1",
                                    "details": [
                                        {
                                            "name": "상세 정보 1",
                                            "synthesis": "상세 설명"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        self.sample_chunk_analysis = {
            "topic": "테스트 토픽",
            "summary": "이것은 테스트 요약입니다.",
            "concepts": ["개념 1", "개념 2", "개념 3"],
            "key_claims": ["주장 1", "주장 2"],
            "questions_raised": ["질문 1", "질문 2"]
        }

    def test_validate_language_codes(self):
        """Test language code validation"""
        # Valid codes
        self.assertTrue(validate_language_codes('ko', 'en'))
        self.assertTrue(validate_language_codes('en', 'ja'))
        self.assertTrue(validate_language_codes('zh-cn', 'ko'))
        
        # Invalid codes
        self.assertFalse(validate_language_codes('xx', 'en'))
        self.assertFalse(validate_language_codes('ko', 'yy'))
        self.assertFalse(validate_language_codes('', 'en'))

    def test_split_text_semantically(self):
        """Test semantic text splitting"""
        # Short text - should not split
        short_text = "This is a short text."
        chunks = split_text_semantically(short_text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)
        
        # Long text with paragraphs
        long_text = "첫 번째 문단.\n\n두 번째 문단.\n\n세 번째 문단." + "추가텍스트" * 1000
        chunks = split_text_semantically(long_text, max_length=100)
        self.assertGreater(len(chunks), 1)
        
        # Text with sentences
        sentence_text = "첫 번째 문장. 두 번째 문장. 세 번째 문장. " + "반복텍스트 " * 200
        chunks = split_text_semantically(sentence_text, max_length=50)
        self.assertGreater(len(chunks), 1)
        
        # Empty text
        empty_chunks = split_text_semantically("")
        self.assertEqual(len(empty_chunks), 1)
        self.assertEqual(empty_chunks[0], "")

    @patch('src.pipeline.translation.requests.post')
    def test_translate_with_retry_success(self, mock_post):
        """Test successful translation with retry"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'result': {
                    'translatedText': 'Hello. Nice to meet you.'
                }
            }
        }
        mock_post.return_value = mock_response
        
        result = translate_with_retry(
            "안녕하세요. 반갑습니다.",
            'ko', 'en',
            self.valid_client_id, self.valid_client_secret
        )
        
        self.assertEqual(result, 'Hello. Nice to meet you.')
        mock_post.assert_called_once()

    @patch('src.pipeline.translation.requests.post')
    def test_translate_with_retry_rate_limit(self, mock_post):
        """Test translation with rate limiting"""
        # Mock rate limit response then success
        mock_response1 = MagicMock()
        mock_response1.status_code = 429
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            'message': {
                'result': {
                    'translatedText': 'Translated text'
                }
            }
        }
        
        mock_post.side_effect = [mock_response1, mock_response2]
        
        result = translate_with_retry(
            "테스트 텍스트",
            'ko', 'en',
            self.valid_client_id, self.valid_client_secret,
            max_retries=3
        )
        
        self.assertEqual(result, 'Translated text')
        self.assertEqual(mock_post.call_count, 2)

    @patch('src.pipeline.translation.requests.post')
    def test_translate_with_retry_failure(self, mock_post):
        """Test translation failure"""
        # Mock persistent failure
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = translate_with_retry(
            "테스트 텍스트",
            'ko', 'en',
            self.valid_client_id, self.valid_client_secret,
            max_retries=2
        )
        
        self.assertIsNone(result)
        self.assertEqual(mock_post.call_count, 2)

    def test_translate_batch_enhanced_same_language(self):
        """Test batch translation with same source and target language"""
        result = translate_batch_enhanced(
            self.sample_texts, 'ko', 'ko',
            self.valid_client_id, self.valid_client_secret
        )
        
        self.assertEqual(result, self.sample_texts)

    def test_translate_batch_enhanced_empty(self):
        """Test batch translation with empty input"""
        result = translate_batch_enhanced([], 'ko', 'en', self.valid_client_id, self.valid_client_secret)
        self.assertEqual(result, [])
        
        result = translate_batch_enhanced(['', '  '], 'ko', 'en', self.valid_client_id, self.valid_client_secret)
        self.assertEqual(result, ['', '  '])

    @patch('src.pipeline.translation.translate_with_retry')
    def test_translate_batch_enhanced_success(self, mock_translate):
        """Test successful batch translation"""
        # Mock translations
        mock_translate.side_effect = [
            "Hello. Nice to meet you.",
            "This is a test sentence.",
            "Python programming language"
        ]
        
        result = translate_batch_enhanced(
            self.sample_texts, 'ko', 'en',
            self.valid_client_id, self.valid_client_secret
        )
        
        self.assertEqual(len(result), len(self.sample_texts))
        self.assertEqual(mock_translate.call_count, len(self.sample_texts))

    @patch('src.pipeline.translation.translate_batch_enhanced')
    def test_translate_structure_enhanced(self, mock_batch_translate):
        """Test structure translation"""
        # Mock batch translation to return translated texts
        mock_batch_translate.return_value = [
            "Test Structure",
            "This is a test structure.",
            "Category 1", 
            "Concept 1",
            "Subconcept 1",
            "Detail Information 1",
            "Detailed Description"
        ]
        
        result = translate_structure_enhanced(
            self.sample_structure, 'ko', 'en',
            self.valid_client_id, self.valid_client_secret
        )
        
        # Check if structure has translation metadata
        self.assertIn('_translation_metadata', result)
        self.assertEqual(result['_translation_metadata']['source_language'], 'ko')
        self.assertEqual(result['_translation_metadata']['target_language'], 'en')
        
        # Verify batch translation was called
        mock_batch_translate.assert_called_once()

    @patch('src.pipeline.translation.translate_batch_enhanced')
    def test_translate_chunk_analysis_enhanced(self, mock_batch_translate):
        """Test chunk analysis translation"""
        # Mock batch translation
        mock_batch_translate.return_value = [
            "Test Topic",
            "This is a test summary.",
            "Concept 1", "Concept 2", "Concept 3",
            "Claim 1", "Claim 2", 
            "Question 1", "Question 2"
        ]
        
        result = translate_chunk_analysis_enhanced(
            self.sample_chunk_analysis, 'ko', 'en',
            self.valid_client_id, self.valid_client_secret
        )
        
        # Check if metadata is added
        self.assertIn('_translation_metadata', result)
        self.assertEqual(result['_translation_metadata']['source_language'], 'ko')
        self.assertEqual(result['_translation_metadata']['target_language'], 'en')
        
        # Verify batch translation was called
        mock_batch_translate.assert_called_once()

    def test_get_translation_supported_languages(self):
        """Test getting supported languages"""
        languages = get_translation_supported_languages()
        self.assertEqual(languages, SUPPORTED_LANGUAGES)
        self.assertIn('ko', languages)
        self.assertIn('en', languages)
        self.assertIn('ja', languages)

    def test_translate_with_retry_empty_text(self):
        """Test translation with empty text"""
        result = translate_with_retry(
            "", 'ko', 'en', 
            self.valid_client_id, self.valid_client_secret
        )
        self.assertEqual(result, "")
        
        result = translate_with_retry(
            "   ", 'ko', 'en',
            self.valid_client_id, self.valid_client_secret
        )
        self.assertEqual(result, "   ")

    def test_translate_structure_enhanced_same_language(self):
        """Test structure translation with same language"""
        result = translate_structure_enhanced(
            self.sample_structure, 'ko', 'ko',
            self.valid_client_id, self.valid_client_secret
        )
        
        # Should return original structure without changes
        self.assertEqual(result, self.sample_structure)

    def test_translate_chunk_analysis_enhanced_same_language(self):
        """Test chunk analysis translation with same language"""
        result = translate_chunk_analysis_enhanced(
            self.sample_chunk_analysis, 'ko', 'ko',
            self.valid_client_id, self.valid_client_secret
        )
        
        # Should return original data without changes
        self.assertEqual(result, self.sample_chunk_analysis)

    @patch('src.pipeline.translation.requests.post')
    def test_translate_with_retry_timeout(self, mock_post):
        """Test translation with timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        result = translate_with_retry(
            "테스트 텍스트",
            'ko', 'en',
            self.valid_client_id, self.valid_client_secret,
            max_retries=2
        )

        self.assertIsNone(result)
        self.assertEqual(mock_post.call_count, 2)

    def test_translate_batch_enhanced_invalid_credentials(self):
        """Test batch translation with invalid credentials"""
        result = translate_batch_enhanced(
            self.sample_texts, 'ko', 'en',
            "", ""  # Empty credentials
        )
        
        # Should return original texts when credentials are invalid
        self.assertEqual(result, self.sample_texts)

    def test_translate_batch_enhanced_unsupported_language(self):
        """Test batch translation with unsupported language"""
        result = translate_batch_enhanced(
            self.sample_texts, 'xx', 'en',  # Invalid source
            self.valid_client_id, self.valid_client_secret
        )
        
        self.assertEqual(result, self.sample_texts)
        
        result = translate_batch_enhanced(
            self.sample_texts, 'ko', 'yy',  # Invalid target
            self.valid_client_id, self.valid_client_secret
        )
        
        self.assertEqual(result, self.sample_texts)


class TestPapagoIntegration(unittest.TestCase):
    """Integration tests for Papago API (requires valid credentials)"""
    
    @classmethod
    def setUpClass(cls):
        """Check if Papago credentials are available for integration tests"""
        cls.has_credentials = all([
            os.getenv('PAPAGO_CLIENT_ID'),
            os.getenv('PAPAGO_CLIENT_SECRET')
        ])
        
        if cls.has_credentials:
            cls.client_id = os.getenv('PAPAGO_CLIENT_ID')
            cls.client_secret = os.getenv('PAPAGO_CLIENT_SECRET')
    
    def test_translate_simple_text_integration(self):
        """Integration test for simple text translation"""
        if not self.has_credentials:
            self.skipTest("Papago credentials not available")
        result = translate_with_retry(
            "안녕하세요",
            'ko', 'en',
            self.client_id or "", self.client_secret or ""
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        print(f"Integration test result: '안녕하세요' -> '{result}'")

    def test_translate_batch_integration(self):
        """Integration test for batch translation"""
        if not self.has_credentials:
            self.skipTest("Papago credentials not available")
        texts = ["감사합니다", "미안합니다", "축하합니다"]
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Papago client ID and secret must be set for integration tests.")
        
        result = translate_batch_enhanced(
            texts, 'ko', 'en',
            self.client_id, self.client_secret
        )
        
        self.assertEqual(len(result), len(texts))
        for translated in result:
            self.assertIsInstance(translated, str)
            self.assertGreater(len(translated), 0)
        
        print("Batch integration test results:")
        for original, translated in zip(texts, result):
            print(f"  '{original}' -> '{translated}'")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2)