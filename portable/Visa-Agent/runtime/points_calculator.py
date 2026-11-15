"""Points Calculator for skilled migration visa pathways (189, 190, 491).

Reference: https://immi.homeaffairs.gov.au/help-support/tools/points-calculator

No external dependencies; all rules deterministic per official calculator.
"""

from typing import Optional, Dict, List, Any


class PointsCalculationError(ValueError):
    """Raised when points cannot be calculated due to invalid input."""
    pass


class PointsCalculator:
    """Calculate points for skilled migration visas: 189 (General), 190 (Nominated), 491 (Regional)."""

    # English test score tables: test -> {score_range: points}
    IELTS_SCORES = {
        8.5: 20, 8.0: 20, 7.5: 20,
        7.0: 10, 6.5: 10,
        6.0: 0,
    }

    TOEFL_SCORES = {
        110: 20, 109: 20, 108: 20, 107: 20, 106: 20, 105: 20, 104: 20, 103: 20, 102: 20, 101: 20, 100: 20, 99: 20, 98: 20, 97: 20, 96: 20, 95: 20, 94: 20,
        93: 10, 92: 10, 91: 10, 90: 10, 89: 10, 88: 10, 87: 10, 86: 10, 85: 10, 84: 10, 83: 10, 82: 10, 81: 10, 80: 10, 79: 10,
        78: 10, 77: 10, 76: 10, 75: 10, 74: 10, 73: 10, 72: 10, 71: 10, 70: 10, 69: 10, 68: 10, 67: 10, 66: 10, 65: 10, 64: 10, 63: 10, 62: 10, 61: 10, 60: 10,
    }

    PTE_SCORES = {
        90: 20, 89: 20, 88: 20, 87: 20, 86: 20, 85: 20, 84: 20, 83: 20, 82: 20, 81: 20, 80: 20, 79: 20,
        78: 10, 77: 10, 76: 10, 75: 10, 74: 10, 73: 10, 72: 10, 71: 10, 70: 10,
        69: 10, 68: 10, 67: 10, 66: 10, 65: 10, 64: 10, 63: 10, 62: 10, 61: 10, 60: 10, 59: 10, 58: 10, 57: 10, 56: 10, 55: 10, 54: 10, 53: 10, 52: 10, 51: 10, 50: 10,
    }

    CAMBRIDGE_SCORES = {
        230: 20, 229: 20, 228: 20, 227: 20, 226: 20, 225: 20, 224: 20, 223: 20, 222: 20, 221: 20, 220: 20, 219: 20, 218: 20, 217: 20, 216: 20, 215: 20, 216: 20, 214: 20, 213: 20, 212: 20, 211: 20, 210: 20, 209: 20, 208: 20, 207: 20, 206: 20, 205: 20, 204: 20, 203: 20, 202: 20, 201: 20, 200: 20, 199: 20, 198: 20, 197: 20, 196: 20, 195: 20, 194: 20, 193: 20, 192: 20, 191: 20, 190: 20, 189: 20, 188: 20, 187: 20, 186: 20, 185: 20,
        184: 20, 183: 20, 182: 20, 181: 20, 180: 20, 179: 20, 178: 20, 177: 20, 176: 20,
        175: 10, 174: 10, 173: 10, 172: 10, 171: 10, 170: 10, 169: 10, 168: 10, 167: 10, 166: 10, 165: 10, 164: 10, 163: 10, 162: 10,
        161: 10, 160: 10, 159: 10, 158: 10, 157: 10, 156: 10, 155: 10, 154: 10, 153: 10, 152: 10, 151: 10, 150: 10, 149: 10, 148: 10, 147: 10,
    }

    OET_SCORES = {
        'A': 20,
        'B': 20,
        'C': 10,
        'D': 0,
    }

    # Age points table
    AGE_BANDS = {
        (18, 24): 25,
        (25, 32): 30,
        (33, 39): 25,
        (40, 44): 15,
        (45, 125): 0,  # 45+
    }

    # Work experience points (Australian + Overseas)
    EXPERIENCE_YEARS = {
        (1, 2): 5,
        (3, 4): 10,
        (5, 7): 15,
        (8, 9): 20,
        (10, 100): 20,  # 10+
    }

    # Qualification points
    QUALIFICATIONS = {
        'doctorate': 15,
        'doctorate_from_australian_university': 15,
        'masters': 15,
        'masters_from_australian_university': 15,
        'bachelor': 15,
        'bachelor_from_australian_university': 15,
        'diploma': 10,
        'diploma_from_australian_university': 10,
        'advanced_diploma': 10,
        'advanced_diploma_from_australian_university': 10,
        'none': 0,
    }

    # Visa-specific cutoff offsets and typical minimums (estimates only)
    VISA_CONFIGS = {
        '189': {'bonus': 0, 'name': 'General Skilled Migration', 'min_estimate': 65},
        '190': {'bonus': 5, 'name': 'State Nominated', 'min_estimate': 60},
        '491': {'bonus': 5, 'name': 'Regional Sponsored', 'min_estimate': 60},
    }

    def __init__(self):
        """Initialize the points calculator."""
        pass

    def age_points(self, age: int) -> int:
        """Calculate age-based points.

        Args:
            age: Applicant age in years (18-125)

        Returns:
            Points awarded for age

        Raises:
            PointsCalculationError: If age is invalid
        """
        if not isinstance(age, int) or age < 18 or age > 125:
            raise PointsCalculationError(f"Age must be integer between 18 and 125, got: {age}")

        for (min_age, max_age), points in self.AGE_BANDS.items():
            if min_age <= age <= max_age:
                return points

        return 0

    def english_points(self, test: str, score: Any) -> int:
        """Calculate English language proficiency points.

        Args:
            test: Test type ('IELTS', 'TOEFL', 'PTE', 'Cambridge', 'OET')
            score: Test score (varies by test type)

        Returns:
            Points awarded for English proficiency

        Raises:
            PointsCalculationError: If test type or score is invalid
        """
        test_lower = test.strip().lower() if isinstance(test, str) else ""

        if test_lower == 'ielts':
            try:
                score_float = float(score)
                # Find closest match in IELTS table (IELTS is in 0.5 increments)
                for ielts_score in sorted(self.IELTS_SCORES.keys(), reverse=True):
                    if score_float >= ielts_score:
                        return self.IELTS_SCORES[ielts_score]
                return self.IELTS_SCORES.get(6.0, 0)
            except (ValueError, TypeError):
                raise PointsCalculationError(f"Invalid IELTS score: {score}")

        elif test_lower == 'toefl':
            try:
                score_int = int(float(score))
                if score_int in self.TOEFL_SCORES:
                    return self.TOEFL_SCORES[score_int]
                # Find closest score below the input
                for toefl_score in sorted(self.TOEFL_SCORES.keys(), reverse=True):
                    if score_int >= toefl_score:
                        return self.TOEFL_SCORES[toefl_score]
                return 0
            except (ValueError, TypeError):
                raise PointsCalculationError(f"Invalid TOEFL score: {score}")

        elif test_lower == 'pte':
            try:
                score_int = int(float(score))
                if score_int in self.PTE_SCORES:
                    return self.PTE_SCORES[score_int]
                # Find closest score below the input
                for pte_score in sorted(self.PTE_SCORES.keys(), reverse=True):
                    if score_int >= pte_score:
                        return self.PTE_SCORES[pte_score]
                return 0
            except (ValueError, TypeError):
                raise PointsCalculationError(f"Invalid PTE score: {score}")

        elif test_lower == 'cambridge':
            try:
                score_int = int(float(score))
                if score_int in self.CAMBRIDGE_SCORES:
                    return self.CAMBRIDGE_SCORES[score_int]
                # Find closest score below the input
                for cam_score in sorted(self.CAMBRIDGE_SCORES.keys(), reverse=True):
                    if score_int >= cam_score:
                        return self.CAMBRIDGE_SCORES[cam_score]
                return 0
            except (ValueError, TypeError):
                raise PointsCalculationError(f"Invalid Cambridge score: {score}")

        elif test_lower == 'oet':
            score_str = str(score).strip().upper()
            if score_str in self.OET_SCORES:
                return self.OET_SCORES[score_str]
            raise PointsCalculationError(f"Invalid OET score: {score}. Must be A, B, C, or D.")

        else:
            raise PointsCalculationError(f"Unknown English test: {test}. Valid: IELTS, TOEFL, PTE, Cambridge, OET")

    def experience_points(self, years: int) -> int:
        """Calculate work experience points (Australian + Overseas combined).

        Args:
            years: Total work experience in years

        Returns:
            Points awarded for work experience

        Raises:
            PointsCalculationError: If years is invalid
        """
        if not isinstance(years, int) or years < 0 or years > 100:
            raise PointsCalculationError(f"Experience years must be integer between 0 and 100, got: {years}")

        if years == 0:
            return 0

        for (min_years, max_years), points in self.EXPERIENCE_YEARS.items():
            if min_years <= years <= max_years:
                return points

        return 0

    def qualification_points(self, level: str) -> int:
        """Calculate qualification points.

        Args:
            level: Qualification level (doctorate, masters, bachelor, diploma, advanced_diploma, none)

        Returns:
            Points awarded for qualification

        Raises:
            PointsCalculationError: If qualification level is invalid
        """
        level_lower = level.strip().lower() if isinstance(level, str) else ""

        if level_lower not in self.QUALIFICATIONS:
            valid = ', '.join(sorted(self.QUALIFICATIONS.keys()))
            raise PointsCalculationError(
                f"Invalid qualification: {level}. Valid: {valid}"
            )

        return self.QUALIFICATIONS[level_lower]

    def spouse_points(self, has_positive_assessment: bool) -> int:
        """Calculate spouse skills assessment points.

        Args:
            has_positive_assessment: True if spouse has positive skills assessment

        Returns:
            Points awarded for spouse assessment (0 or 5)
        """
        return 5 if has_positive_assessment else 0

    def _calculate_base_points(self, client: dict) -> Dict[str, int]:
        """Calculate all component points for a client.

        Args:
            client: Client data dict with keys: age, english_test, english_score,
                   experience_years, qualification, spouse_assessment (optional)

        Returns:
            Dict with component points: age, english, experience, qualification, spouse

        Raises:
            PointsCalculationError: If required fields are missing or invalid
        """
        required_fields = ['age', 'english_test', 'english_score', 'experience_years', 'qualification']
        missing = [f for f in required_fields if f not in client]
        if missing:
            raise PointsCalculationError(f"Missing required fields: {', '.join(missing)}")

        points = {
            'age': self.age_points(client['age']),
            'english': self.english_points(client['english_test'], client['english_score']),
            'experience': self.experience_points(client['experience_years']),
            'qualification': self.qualification_points(client['qualification']),
            'spouse': self.spouse_points(client.get('spouse_assessment', False)),
        }

        return points

    def calculate_189(self, client: dict) -> dict:
        """Calculate points for 189 General Skilled Migration visa.

        Args:
            client: Client data dict with age, english_test, english_score,
                   experience_years, qualification, optional spouse_assessment

        Returns:
            Dict with visa_type, total_points, breakdown (by component),
            and metadata (visa_name, visa_bonus)
        """
        try:
            points = self._calculate_base_points(client)
        except PointsCalculationError as e:
            raise PointsCalculationError(f"189 calculation failed: {e}") from None

        total = sum(points.values())
        config = self.VISA_CONFIGS['189']

        return {
            'visa_type': '189',
            'visa_name': config['name'],
            'total_points': total,
            'breakdown': {
                'age': points['age'],
                'english': points['english'],
                'experience': points['experience'],
                'qualification': points['qualification'],
                'spouse': points['spouse'],
                'visa_bonus': 0,
            },
            'metadata': {
                'visa_bonus': config['bonus'],
                'estimated_minimum_cutoff': config['min_estimate'],
            }
        }

    def calculate_190(self, client: dict, state: str = '') -> dict:
        """Calculate points for 190 State Nominated visa.

        Args:
            client: Client data dict with age, english_test, english_score,
                   experience_years, qualification, optional spouse_assessment
            state: State/territory code (optional, for reference only)

        Returns:
            Dict with visa_type, total_points, breakdown including +5 state bonus,
            and metadata
        """
        try:
            points = self._calculate_base_points(client)
        except PointsCalculationError as e:
            raise PointsCalculationError(f"190 calculation failed: {e}") from None

        base_total = sum(points.values())
        config = self.VISA_CONFIGS['190']
        visa_bonus = config['bonus']
        total = base_total + visa_bonus

        return {
            'visa_type': '190',
            'visa_name': config['name'],
            'state': state.strip() if state else 'unspecified',
            'total_points': total,
            'breakdown': {
                'age': points['age'],
                'english': points['english'],
                'experience': points['experience'],
                'qualification': points['qualification'],
                'spouse': points['spouse'],
                'visa_bonus': visa_bonus,
            },
            'metadata': {
                'visa_bonus': visa_bonus,
                'estimated_minimum_cutoff': config['min_estimate'],
                'note': 'Must be nominated by a State or Territory'
            }
        }

    def calculate_491(self, client: dict, state: str = '') -> dict:
        """Calculate points for 491 Regional Sponsored visa.

        Args:
            client: Client data dict with age, english_test, english_score,
                   experience_years, qualification, optional spouse_assessment
            state: State/territory code (optional, for reference only)

        Returns:
            Dict with visa_type, total_points, breakdown showing regional bonus,
            and metadata
        """
        try:
            points = self._calculate_base_points(client)
        except PointsCalculationError as e:
            raise PointsCalculationError(f"491 calculation failed: {e}") from None

        base_total = sum(points.values())
        config = self.VISA_CONFIGS['491']
        visa_bonus = config['bonus']  # +5 net (provisional -10, regional +15)
        total = base_total + visa_bonus

        return {
            'visa_type': '491',
            'visa_name': config['name'],
            'state': state.strip() if state else 'unspecified',
            'total_points': total,
            'breakdown': {
                'age': points['age'],
                'english': points['english'],
                'experience': points['experience'],
                'qualification': points['qualification'],
                'spouse': points['spouse'],
                'visa_bonus': visa_bonus,
            },
            'metadata': {
                'visa_bonus': visa_bonus,
                'provisional_reduction': -10,
                'regional_bonus': 15,
                'estimated_minimum_cutoff': config['min_estimate'],
                'note': 'Provisional visa; eligible for 191 after 3 years in designated region'
            }
        }

    def generate_scenarios(self, client: dict, visa: str) -> list:
        """Generate 'what if' scenarios by improving specific components.

        Args:
            client: Client data dict
            visa: Visa type ('189', '190', '491')

        Returns:
            List of scenario dicts showing impact of improvements
        """
        if visa not in self.VISA_CONFIGS:
            raise PointsCalculationError(f"Unknown visa type: {visa}")

        scenarios = []

        # Scenario 1: Improve English
        for test_name in ['IELTS', 'TOEFL', 'PTE', 'Cambridge', 'OET']:
            test_lower = test_name.lower()
            original_test = client.get('english_test', '').lower()

            # Only suggest targets they haven't reached
            if original_test == test_lower:
                continue

            client_copy = client.copy()
            client_copy['english_test'] = test_name

            if test_lower == 'ielts':
                client_copy['english_score'] = 8.0
            elif test_lower == 'toefl':
                client_copy['english_score'] = 94
            elif test_lower == 'pte':
                client_copy['english_score'] = 79
            elif test_lower == 'cambridge':
                client_copy['english_score'] = 185
            elif test_lower == 'oet':
                client_copy['english_score'] = 'A'

            try:
                if visa == '189':
                    result = self.calculate_189(client_copy)
                elif visa == '190':
                    result = self.calculate_190(client_copy, client.get('state', ''))
                else:
                    result = self.calculate_491(client_copy, client.get('state', ''))

                scenarios.append({
                    'type': 'english_improvement',
                    'description': f'Switch to {test_name} with minimum qualifying score',
                    'change_points': result['total_points'] - self._get_current_points(client, visa),
                    'new_total': result['total_points'],
                    'english_test': test_name,
                })
            except PointsCalculationError:
                pass

        # Scenario 2: Additional experience
        for extra_years in [1, 2, 3]:
            client_copy = client.copy()
            original_exp = client.get('experience_years', 0)
            client_copy['experience_years'] = original_exp + extra_years

            try:
                if visa == '189':
                    result = self.calculate_189(client_copy)
                elif visa == '190':
                    result = self.calculate_190(client_copy, client.get('state', ''))
                else:
                    result = self.calculate_491(client_copy, client.get('state', ''))

                scenarios.append({
                    'type': 'experience_improvement',
                    'description': f'Gain {extra_years} more years of work experience',
                    'change_points': result['total_points'] - self._get_current_points(client, visa),
                    'new_total': result['total_points'],
                    'new_experience_years': original_exp + extra_years,
                })
            except PointsCalculationError:
                pass

        # Scenario 3: Spouse assessment (if not already positive)
        if not client.get('spouse_assessment', False):
            client_copy = client.copy()
            client_copy['spouse_assessment'] = True

            try:
                if visa == '189':
                    result = self.calculate_189(client_copy)
                elif visa == '190':
                    result = self.calculate_190(client_copy, client.get('state', ''))
                else:
                    result = self.calculate_491(client_copy, client.get('state', ''))

                scenarios.append({
                    'type': 'spouse_assessment',
                    'description': 'Spouse obtains positive skills assessment',
                    'change_points': 5,
                    'new_total': result['total_points'],
                })
            except PointsCalculationError:
                pass

        return scenarios

    def _get_current_points(self, client: dict, visa: str) -> int:
        """Helper: get current total points for a visa type."""
        try:
            if visa == '189':
                return self.calculate_189(client)['total_points']
            elif visa == '190':
                return self.calculate_190(client)['total_points']
            else:
                return self.calculate_491(client)['total_points']
        except PointsCalculationError:
            return 0

    def get_current_cutoffs(self) -> dict:
        """Return current invitation round cutoff points (estimated).

        Returns:
            Dict with visa types and estimated minimum cutoff points
        """
        return {
            '189': self.VISA_CONFIGS['189']['min_estimate'],
            '190': self.VISA_CONFIGS['190']['min_estimate'],
            '491': self.VISA_CONFIGS['491']['min_estimate'],
        }

    def assess_likelihood(self, visa: str, points: int, cutoff: Optional[int] = None) -> str:
        """Assess likelihood of invitation based on points and cutoff.

        Args:
            visa: Visa type ('189', '190', '491')
            points: Applicant's total points
            cutoff: Current cutoff points (if None, uses estimated current cutoff)

        Returns:
            Likelihood assessment string: 'high', 'moderate', 'low', or 'very_low'
        """
        if visa not in self.VISA_CONFIGS:
            raise PointsCalculationError(f"Unknown visa type: {visa}")

        if cutoff is None:
            cutoff = self.VISA_CONFIGS[visa]['min_estimate']

        # Assessment logic (more conservative thresholds)
        if points >= cutoff + 10:
            return 'high'
        elif points >= cutoff + 5:
            return 'moderate'
        elif points >= cutoff:
            return 'low'
        else:
            return 'very_low'

    def calculate_all(self, client: dict) -> dict:
        """Calculate points for all three visa types.

        Args:
            client: Client data dict

        Returns:
            Dict with results for 189, 190, 491, and comparison metadata
        """
        results_189 = self.calculate_189(client)
        results_190 = self.calculate_190(client, client.get('state', ''))
        results_491 = self.calculate_491(client, client.get('state', ''))

        return {
            'occupation_code': client.get('occupation_code', 'unspecified'),
            'visa_189': results_189,
            'visa_190': results_190,
            'visa_491': results_491,
            'recommended_visa': self._recommend_visa(results_189, results_190, results_491),
            'version': '1.0.0',
            'disclaimer': 'These are estimates based on official Home Affairs rules. Not an official EOI. Always verify with current calculator at https://immi.homeaffairs.gov.au/help-support/tools/points-calculator',
        }

    def _recommend_visa(self, res_189: dict, res_190: dict, res_491: dict) -> str:
        """Recommend visa pathway based on points."""
        cutoffs = self.get_current_cutoffs()
        candidates = []

        if res_189['total_points'] >= cutoffs['189']:
            candidates.append(('189', res_189['total_points']))

        if res_190['total_points'] >= cutoffs['190']:
            candidates.append(('190', res_190['total_points']))

        if res_491['total_points'] >= cutoffs['491']:
            candidates.append(('491', res_491['total_points']))

        if not candidates:
            # Not meeting any cutoff; recommend highest points
            points = [res_189['total_points'], res_190['total_points'], res_491['total_points']]
            if max(points) == res_189['total_points']:
                return '189'
            elif max(points) == res_190['total_points']:
                return '190'
            else:
                return '491'

        # Sort by points descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]


def validate_client_data(client: dict) -> None:
    """Validate client data structure.

    Raises:
        PointsCalculationError: If data is invalid or incomplete
    """
    required = ['age', 'english_test', 'english_score', 'experience_years', 'qualification']
    missing = [f for f in required if f not in client]
    if missing:
        raise PointsCalculationError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(client['age'], int):
        raise PointsCalculationError("age must be an integer")

    if not isinstance(client['experience_years'], int):
        raise PointsCalculationError("experience_years must be an integer")

    if not isinstance(client['english_test'], str):
        raise PointsCalculationError("english_test must be a string")

    if not isinstance(client['qualification'], str):
        raise PointsCalculationError("qualification must be a string")
