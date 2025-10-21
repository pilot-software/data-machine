import pytest
from unittest.mock import Mock, patch
from app.services.terminology_service import TerminologyService
from app.repositories.icd10_repository import ICD10Repository
from app.db.models import ICD10

class TestArchitectureSeparation:
    """Test that architecture layers are properly separated"""
    
    @pytest.mark.asyncio
    async def test_service_uses_repository_only(self):
        """Test that service layer only uses repository, not direct DB access"""
        service = TerminologyService()
        
        with patch('app.repositories.icd10_repository.ICD10Repository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value.__enter__.return_value = mock_repo
            mock_repo_class.return_value.__exit__.return_value = None
            
            mock_repo.find_by_code_prefix.return_value = []
            mock_repo.find_by_term_prefix.return_value = []
            mock_repo.find_by_similarity.return_value = []
            
            with patch('app.services.redis_service.redis_service') as mock_redis:
                mock_redis.get.return_value = None
                mock_redis.set.return_value = True
                
                result = await service.search_icd10("test", limit=10)
                
                mock_repo.find_by_code_prefix.assert_called()
                mock_repo.find_by_term_prefix.assert_called()
                mock_repo.find_by_similarity.assert_called()
    
    def test_repository_returns_models_only(self):
        """Test that repository returns only database models"""
        with patch('app.db.database.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            mock_result = ICD10()
            mock_result.code = "E11.9"
            mock_result.term = "Type 2 diabetes"
            mock_result.active = True
            
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_result]
            
            repo = ICD10Repository()
            repo.db = mock_db
            
            results = repo.find_by_code_prefix("E11")
            
            assert len(results) == 1
            assert isinstance(results[0], ICD10)
            assert results[0].code == "E11.9"
    
    def test_no_direct_db_access_in_service(self):
        """Test that service layer doesn't directly access database"""
        import inspect
        from app.services.terminology_service import TerminologyService
        
        source = inspect.getsource(TerminologyService)
        
        assert 'SessionLocal' not in source
        assert 'from app.db.database import' not in source
        assert 'db.query' not in source
    
    def test_repository_context_manager(self):
        """Test that repository properly manages database connections"""
        with patch('app.db.database.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            
            with ICD10Repository() as repo:
                assert repo.db == mock_db
            
            mock_db.close.assert_called_once()

class TestBusinessLogicSeparation:
    """Test that business logic is properly separated"""
    
    def test_confidence_calculation_in_service(self):
        """Test that confidence calculation is in service layer"""
        service = TerminologyService()
        
        mock_result = Mock()
        mock_result.term = "Type 2 diabetes mellitus"
        
        confidence = service._calculate_confidence(mock_result, "diabetes")
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_search_algorithm_in_service(self):
        """Test that search algorithm logic is in service layer"""
        service = TerminologyService()
        
        assert hasattr(service, '_format_result')
        assert hasattr(service, '_calculate_confidence')
        assert hasattr(service, '_matches_chapter')
        assert hasattr(service, '_analyze_symptom_matches')
    
    @pytest.mark.asyncio
    async def test_caching_logic_in_service(self):
        """Test that caching decisions are made in service layer"""
        with patch('app.services.redis_service.redis_service') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            
            service = TerminologyService()
            
            with patch('app.repositories.icd10_repository.ICD10Repository') as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value.__enter__.return_value = mock_repo
                mock_repo_class.return_value.__exit__.return_value = None
                
                mock_repo.find_by_code_prefix.return_value = []
                mock_repo.find_by_term_prefix.return_value = []
                mock_repo.find_by_similarity.return_value = []
                
                await service.search_icd10("test")
                
                mock_redis.get.assert_called()
                mock_redis.set.assert_called()

if __name__ == "__main__":
    pytest.main([__file__])