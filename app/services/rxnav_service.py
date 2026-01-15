"""
RxNav API Service - FREE Drug Interaction Checking
No API key required - provided by U.S. National Library of Medicine
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class RxNavService:
    """Service for checking drug interactions using RxNav API"""
    
    BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HMS-Clinical-AI/1.0'})
    
    @lru_cache(maxsize=1000)
    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """Get RxCUI (RxNorm Concept Unique Identifier) for a drug name"""
        try:
            url = f"{self.BASE_URL}/rxcui.json"
            params = {'name': drug_name}
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            rxcui_list = data.get('idGroup', {}).get('rxnormId', [])
            
            if rxcui_list:
                return rxcui_list[0]  # Return first match
            
            logger.warning(f"No RxCUI found for drug: {drug_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting RxCUI for {drug_name}: {e}")
            return None
    
    def check_drug_interactions(self, drug_names: List[str]) -> Dict[str, Any]:
        """Check interactions between multiple drugs"""
        start_time = time.time()
        
        # Get RxCUIs for all drugs
        rxcuis = []
        drug_mapping = {}
        
        for drug_name in drug_names:
            rxcui = self.get_rxcui(drug_name)
            if rxcui:
                rxcuis.append(rxcui)
                drug_mapping[rxcui] = drug_name
        
        if len(rxcuis) < 2:
            return {
                'status': 'insufficient_drugs',
                'interactions': [],
                'api_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        
        # Check interactions
        interactions = []
        
        try:
            url = f"{self.BASE_URL}/interaction/list.json"
            params = {'rxcuis': '+'.join(rxcuis)}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            interaction_list = data.get('fullInteractionTypeGroup', [])
            
            for group in interaction_list:
                for interaction_type in group.get('fullInteractionType', []):
                    for interaction in interaction_type.get('interactionPair', []):
                        interactions.append({
                            'drug1': drug_mapping.get(
                                interaction['interactionConcept'][0]['minConceptItem']['rxcui'],
                                'Unknown'
                            ),
                            'drug2': drug_mapping.get(
                                interaction['interactionConcept'][1]['minConceptItem']['rxcui'],
                                'Unknown'
                            ),
                            'severity': interaction.get('severity', 'Unknown'),
                            'description': interaction.get('description', '')
                        })
            
            return {
                'status': 'completed',
                'interactions': interactions,
                'total_interactions': len(interactions),
                'api_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
        except Exception as e:
            logger.error(f"Error checking interactions: {e}")
            return {
                'status': 'api_error',
                'error': str(e),
                'interactions': [],
                'api_time_ms': round((time.time() - start_time) * 1000, 2)
            }
    
    def check_single_drug_interactions(self, drug_name: str) -> Dict[str, Any]:
        """Check all known interactions for a single drug"""
        rxcui = self.get_rxcui(drug_name)
        
        if not rxcui:
            return {
                'status': 'drug_not_found',
                'interactions': []
            }
        
        try:
            url = f"{self.BASE_URL}/interaction/interaction.json"
            params = {'rxcui': rxcui}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            interaction_list = data.get('interactionTypeGroup', [])
            
            interactions = []
            for group in interaction_list:
                for interaction_type in group.get('interactionType', []):
                    for interaction in interaction_type.get('interactionPair', []):
                        interactions.append({
                            'interacts_with': interaction['interactionConcept'][1]['minConceptItem']['name'],
                            'severity': interaction.get('severity', 'Unknown'),
                            'description': interaction.get('description', '')
                        })
            
            return {
                'status': 'completed',
                'drug': drug_name,
                'interactions': interactions,
                'total_interactions': len(interactions)
            }
            
        except Exception as e:
            logger.error(f"Error checking interactions for {drug_name}: {e}")
            return {
                'status': 'api_error',
                'error': str(e),
                'interactions': []
            }
    
    def validate_drug_list(self, drugs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a list of drugs and check for interactions"""
        
        # Extract generic names
        drug_names = []
        for drug in drugs:
            generic_name = drug.get('generic_name', '')
            # Extract base drug name (remove dosage info)
            base_name = generic_name.split()[0] if generic_name else ''
            if base_name:
                drug_names.append(base_name.lower())
        
        if not drug_names:
            return {
                'status': 'no_drugs',
                'interactions': [],
                'warnings': []
            }
        
        # Check interactions
        result = self.check_drug_interactions(drug_names)
        
        # Generate warnings for high-severity interactions
        warnings = []
        for interaction in result.get('interactions', []):
            if interaction.get('severity') in ['high', 'severe', 'contraindicated']:
                warnings.append(
                    f"HIGH SEVERITY: {interaction['drug1']} + {interaction['drug2']} - "
                    f"{interaction.get('description', 'Interaction detected')}"
                )
        
        return {
            'status': result['status'],
            'interactions': result.get('interactions', []),
            'warnings': warnings,
            'api_time_ms': result.get('api_time_ms', 0)
        }


# Global instance
rxnav_service = RxNavService()
