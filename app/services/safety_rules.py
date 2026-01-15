"""
Clinical Safety Rules Engine
Configurable rules for drug contraindications, dosing, and ICD code validation
"""

from typing import Dict, List, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class SafetyRule:
    """Base class for safety rules"""
    
    def __init__(self, rule_id: str, description: str, severity: str = "high"):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity  # critical, high, medium, low
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate rule and return action"""
        raise NotImplementedError


class DrugContraindicationRule(SafetyRule):
    """Rule to exclude drugs based on contraindications"""
    
    def __init__(self, rule_id: str, drug_keywords: List[str], 
                 contraindication_keywords: List[str], description: str):
        super().__init__(rule_id, description, severity="critical")
        self.drug_keywords = [k.lower() for k in drug_keywords]
        self.contraindication_keywords = [k.lower() for k in contraindication_keywords]
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if contraindication exists"""
        red_flags = [rf.lower() for rf in context.get("red_flags", [])]
        diff_diagnoses = [dd.lower() for dd in context.get("differential_diagnoses", [])]
        all_text = red_flags + diff_diagnoses + [context.get("prompt", "").lower()]
        
        has_contraindication = any(
            keyword in text 
            for keyword in self.contraindication_keywords 
            for text in all_text
        )
        
        if has_contraindication:
            return {
                "action": "exclude_drugs",
                "drug_keywords": self.drug_keywords,
                "reason": self.description,
                "triggered": True
            }
        
        return {"triggered": False}


class PediatricDosingRule(SafetyRule):
    """Rule for pediatric dosing requirements"""
    
    def __init__(self, age_threshold: int = 12):
        super().__init__(
            "pediatric_dosing",
            f"Patients under {age_threshold} require pediatric formulations and weight-based dosing",
            severity="critical"
        )
        self.age_threshold = age_threshold
        self.adult_dose_patterns = [
            r'\b(500|600|650|850|1000)\s*mg\b',
            r'\b1\s*g\b',
            r'\btablet\b(?!.*suspension)',
        ]
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if patient is pediatric"""
        patient_age = self._extract_age(context.get("prompt", ""))
        
        if patient_age and patient_age < self.age_threshold:
            return {
                "action": "enforce_pediatric",
                "patient_age": patient_age,
                "exclude_patterns": self.adult_dose_patterns,
                "require_instruction": "Pediatric dose by weight (consult pediatric guidelines)",
                "triggered": True
            }
        
        return {"triggered": False}
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract patient age from text"""
        age_patterns = [
            r'(\d+)\s*year',
            r'(\d+)\s*साल',
            r'(\d+)\s*वर्ष',
            r'(\d+)\s*año'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None


class ICDCodeCorrectionRule(SafetyRule):
    """Rule to correct ICD codes based on context"""
    
    def __init__(self, rule_id: str, condition_keywords: List[str], 
                 wrong_codes: List[str], correct_code: str, description: str):
        super().__init__(rule_id, description, severity="high")
        self.condition_keywords = [k.lower() for k in condition_keywords]
        self.wrong_codes = [c.upper() for c in wrong_codes]
        self.correct_code = correct_code.upper()
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if ICD code needs correction"""
        prompt = context.get("prompt", "").lower()
        diagnosis = context.get("primary_diagnosis", "").lower()
        
        has_condition = any(keyword in prompt or keyword in diagnosis 
                           for keyword in self.condition_keywords)
        
        if has_condition:
            return {
                "action": "correct_icd_code",
                "wrong_codes": self.wrong_codes,
                "correct_code": self.correct_code,
                "reason": self.description,
                "triggered": True
            }
        
        return {"triggered": False}


class RenalDosingRule(SafetyRule):
    """Rule for renal dosing adjustments"""
    
    def __init__(self):
        super().__init__(
            "renal_dosing",
            "Patients with CKD require dose adjustment or drug exclusion",
            severity="critical"
        )
        self.egfr_patterns = [
            r'egfr\s*[<]?\s*(\d+)',
            r'gfr\s*[<]?\s*(\d+)',
        ]
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check renal function"""
        prompt = context.get("prompt", "").lower()
        egfr = self._extract_egfr(prompt)
        
        if egfr:
            if egfr < 30:
                return {
                    "action": "exclude_drugs",
                    "drug_keywords": ["metformin"],
                    "reason": f"eGFR {egfr} < 30: Metformin contraindicated",
                    "triggered": True
                }
            elif egfr < 45:
                return {
                    "action": "add_warning",
                    "warning": f"eGFR {egfr}: Monitor for lactic acidosis if using Metformin",
                    "triggered": True
                }
        
        return {"triggered": False}
    
    def _extract_egfr(self, text: str) -> Optional[int]:
        """Extract eGFR value"""
        for pattern in self.egfr_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None


class ToxicSyndromeRule(SafetyRule):
    """Rule for toxic syndromes with antidote recommendations"""
    
    def __init__(self, syndrome: str, keywords: List[str], antidotes: List[str], 
                 exclude_drugs: List[str], description: str):
        super().__init__(f"toxic_{syndrome}", description, severity="critical")
        self.syndrome = syndrome
        self.keywords = [k.lower() for k in keywords]
        self.antidotes = antidotes
        self.exclude_drugs = [d.lower() for d in exclude_drugs]
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if toxic syndrome is present"""
        diagnosis = context.get("primary_diagnosis", "").lower()
        red_flags = [rf.lower() for rf in context.get("red_flags", [])]
        diff_diagnoses = [dd.lower() for dd in context.get("differential_diagnoses", [])]
        
        all_text = [diagnosis] + red_flags + diff_diagnoses
        
        has_syndrome = any(
            keyword in text 
            for keyword in self.keywords 
            for text in all_text
        )
        
        if has_syndrome:
            return {
                "action": "toxic_syndrome",
                "syndrome": self.syndrome,
                "exclude_drugs": self.exclude_drugs,
                "recommend_antidotes": self.antidotes,
                "reason": self.description,
                "triggered": True
            }
        
        return {"triggered": False}


class PregnancySafetyRule(SafetyRule):
    """Rule for pregnancy-related safety"""
    
    def __init__(self):
        super().__init__(
            "pregnancy_safety",
            "Pregnant patients require pregnancy-safe medications",
            severity="critical"
        )
        self.pregnancy_keywords = ['pregnant', 'pregnancy', 'gestation', 'gestational']
        self.contraindicated_drugs = ['ace inhibitor', 'arb', 'statin', 'warfarin']
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if patient is pregnant"""
        prompt = context.get("prompt", "").lower()
        
        is_pregnant = any(keyword in prompt for keyword in self.pregnancy_keywords)
        
        if is_pregnant:
            return {
                "action": "exclude_drugs",
                "drug_keywords": self.contraindicated_drugs,
                "reason": "Contraindicated in pregnancy",
                "add_warning": "Verify pregnancy category for all medications",
                "triggered": True
            }
        
        return {"triggered": False}


class SafetyRulesEngine:
    """Main safety rules engine"""
    
    def __init__(self):
        self.rules: List[SafetyRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default safety rules"""
        
        # Rule 1: Metformin + Lactic Acidosis
        self.rules.append(DrugContraindicationRule(
            rule_id="metformin_lactic_acidosis",
            drug_keywords=["metformin"],
            contraindication_keywords=["lactic acidosis", "lactate", "acidosis"],
            description="Metformin contraindicated with lactic acidosis risk"
        ))
        
        # Rule 2: Serotonin Syndrome
        self.rules.append(DrugContraindicationRule(
            rule_id="serotonin_syndrome_exclusion",
            drug_keywords=["sertraline", "fluoxetine", "paroxetine", "dextromethorphan", "ssri"],
            contraindication_keywords=["serotonin syndrome", "serotonergic toxicity"],
            description="Exclude causative drugs in serotonin syndrome"
        ))
        
        # Rule 3: Serotonin Syndrome Antidotes
        self.rules.append(ToxicSyndromeRule(
            syndrome="serotonin_syndrome",
            keywords=["serotonin syndrome", "serotonergic toxicity"],
            antidotes=["cyproheptadine", "lorazepam", "diazepam"],
            exclude_drugs=["ssri", "snri", "dextromethorphan", "sertraline"],
            description="Serotonin syndrome requires antidotes and exclusion of causative agents"
        ))
        
        # Rule 4: Metformin + Severe CKD
        self.rules.append(DrugContraindicationRule(
            rule_id="metformin_ckd",
            drug_keywords=["metformin"],
            contraindication_keywords=["egfr < 30", "gfr < 30", "stage 4 ckd", "stage 5 ckd"],
            description="Metformin contraindicated with eGFR < 30"
        ))
        
        # Rule 3: Pediatric dosing
        self.rules.append(PediatricDosingRule(age_threshold=12))
        
        # Rule 4: Gestational Diabetes ICD code
        self.rules.append(ICDCodeCorrectionRule(
            rule_id="gdm_icd_code",
            condition_keywords=["gestational diabetes", "gdm"],
            wrong_codes=["E11", "E119", "E10", "E109"],
            correct_code="O24419",
            description="Gestational diabetes requires O24.4 code, not E11"
        ))
        
        # Rule 4b: Pregnancy Hypertension ICD code
        self.rules.append(ICDCodeCorrectionRule(
            rule_id="pregnancy_hypertension_icd",
            condition_keywords=["hypertension in pregnancy", "pregnancy hypertension", "pregnant"],
            wrong_codes=["I10", "I11", "I12", "I13", "I15"],
            correct_code="O139",
            description="Hypertension in pregnancy requires O139 (gestational hypertension), not I10"
        ))
        
        # Rule 5: Renal dosing
        self.rules.append(RenalDosingRule())
        
        # Rule 6: Pregnancy safety
        self.rules.append(PregnancySafetyRule())
        
        # Rule 7: NSAID + Asthma (ALL NSAIDs)
        self.rules.append(DrugContraindicationRule(
            rule_id="nsaid_asthma_cross_sensitivity",
            drug_keywords=["aspirin", "ibuprofen", "naproxen", "diclofenac", "ketorolac"],
            contraindication_keywords=["asthma", "दम्याचा", "bronchospasm"],
            description="All NSAIDs contraindicated in aspirin-sensitive asthma"
        ))
        
        # Rule 8: Paracetamol + Cirrhosis
        self.rules.append(DrugContraindicationRule(
            rule_id="paracetamol_cirrhosis",
            drug_keywords=["paracetamol", "acetaminophen"],
            contraindication_keywords=["cirrhosis", "alcoholic hepatitis", "liver failure"],
            description="Paracetamol max 2g/day in cirrhosis (not 4g) - HIGH RISK"
        ))
    
    def add_rule(self, rule: SafetyRule):
        """Add custom rule"""
        self.rules.append(rule)
        logger.info(f"Added safety rule: {rule.rule_id}")
    
    def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all rules and return combined actions"""
        results = {
            "drugs_to_exclude": set(),
            "icd_corrections": {},
            "warnings": [],
            "pediatric_required": False,
            "pediatric_age": None,
            "dosage_instructions": {},
            "antidotes_recommended": [],
            "rules_triggered": []
        }
        
        for rule in self.rules:
            try:
                evaluation = rule.evaluate(context)
                
                if evaluation.get("triggered"):
                    results["rules_triggered"].append({
                        "rule_id": rule.rule_id,
                        "description": rule.description,
                        "severity": rule.severity
                    })
                    
                    action = evaluation.get("action")
                    
                    # CRITICAL FIX: Only log rules that actually affect the current drugs/diagnosis
                    if action == "exclude_drugs":
                        excluded_keywords = evaluation.get("drug_keywords", [])
                        # Check if any of these drugs are actually in the context
                        drugs_in_context = any(
                            keyword in context.get("prompt", "").lower()
                            for keyword in excluded_keywords
                        )
                        if not drugs_in_context:
                            # Remove this rule from triggered list - it's a ghost trigger
                            results["rules_triggered"].pop()
                            continue
                        
                        results["drugs_to_exclude"].update(excluded_keywords)
                        if "reason" in evaluation:
                            results["warnings"].append(evaluation["reason"])
                    
                    elif action == "correct_icd_code":
                        for wrong_code in evaluation.get("wrong_codes", []):
                            results["icd_corrections"][wrong_code] = evaluation.get("correct_code")
                    
                    elif action == "enforce_pediatric":
                        results["pediatric_required"] = True
                        results["pediatric_age"] = evaluation.get("patient_age")
                        results["exclude_patterns"] = evaluation.get("exclude_patterns", [])
                        results["dosage_instructions"]["default"] = evaluation.get("require_instruction")
                    
                    elif action == "add_warning":
                        results["warnings"].append(evaluation.get("warning"))
                    
                    elif action == "toxic_syndrome":
                        results["drugs_to_exclude"].update(evaluation.get("exclude_drugs", []))
                        results["antidotes_recommended"].extend(evaluation.get("recommend_antidotes", []))
                        results["warnings"].append(evaluation.get("reason"))
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        return results
    
    def apply_filters(self, drugs: List[Dict], icd_codes: List[str], 
                     context: Dict[str, Any]) -> tuple:
        """Apply safety filters to drugs and ICD codes"""
        
        safety_results = self.evaluate_all(context)
        
        # Filter drugs
        filtered_drugs = []
        for drug in drugs:
            drug_name = drug.get("generic_name", "").lower()
            brand_name = drug.get("brand_name", "").lower()
            
            # Check exclusions
            should_exclude = any(
                keyword in drug_name or keyword in brand_name
                for keyword in safety_results["drugs_to_exclude"]
            )
            
            if should_exclude:
                logger.info(f"Excluded drug: {drug.get('brand_name')} due to safety rules")
                continue
            
            # Check pediatric patterns
            if safety_results["pediatric_required"]:
                exclude_patterns = safety_results.get("exclude_patterns", [])
                if any(re.search(pattern, brand_name) for pattern in exclude_patterns):
                    logger.info(f"Excluded adult formulation: {drug.get('brand_name')}")
                    continue
                
                # Add dosage instruction
                if "dosage_instructions" in safety_results:
                    drug["dosage_instruction"] = safety_results["dosage_instructions"].get("default")
            
            filtered_drugs.append(drug)
        
        # Correct ICD codes
        corrected_icd_codes = []
        for code in icd_codes:
            normalized = code.replace(".", "").upper()
            corrected = safety_results["icd_corrections"].get(normalized, normalized)
            corrected_icd_codes.append(corrected)
        
        return filtered_drugs, corrected_icd_codes, safety_results


# Global instance
safety_engine = SafetyRulesEngine()
