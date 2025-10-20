"""
Trading Signals Engine - Generate buy/sell recommendations based on multiple factors
"""

from typing import Dict, List, Optional
from datetime import datetime


class TradingSignalsEngine:
    """Generate trading signals based on fundamental, technical, and relative strength data"""
    
    # Signal thresholds
    STRONG_BUY_THRESHOLD = 80
    BUY_THRESHOLD = 60
    HOLD_THRESHOLD = 40
    SELL_THRESHOLD = 20
    
    def __init__(self):
        pass
    
    def generate_signal(self, stock_data: Dict, metrics_data: Dict) -> Dict:
        """
        Generate trading signal for a single stock
        
        Args:
            stock_data: Dictionary with stock basic info
            metrics_data: Dictionary with stock metrics (EPS, RS, EMAs)
            
        Returns:
            Dictionary with signal details
        """
        # Calculate individual component scores
        fundamental_score = self._calculate_fundamental_score(metrics_data)
        technical_score = self._calculate_technical_score(metrics_data)
        relative_strength_score = self._calculate_rs_score(metrics_data)
        
        # Calculate weighted total score (0-100)
        total_score = (
            fundamental_score * 0.40 +  # 40% weight on fundamentals
            technical_score * 0.40 +     # 40% weight on technicals
            relative_strength_score * 0.20  # 20% weight on relative strength
        )
        
        # Determine signal type
        signal_type = self._determine_signal_type(total_score)
        
        # Calculate confidence level
        confidence = self._calculate_confidence(
            fundamental_score, 
            technical_score, 
            relative_strength_score
        )
        
        # Generate reasoning text
        reasoning = self._generate_reasoning(
            signal_type,
            metrics_data,
            fundamental_score,
            technical_score,
            relative_strength_score
        )
        
        return {
            'symbol': stock_data.get('symbol'),
            'company_name': stock_data.get('company_name'),
            'sector': stock_data.get('sector'),
            'current_price': stock_data.get('current_price'),
            'signal_type': signal_type,
            'signal_score': round(total_score, 1),
            'confidence': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'fundamental_score': round(fundamental_score, 1),
            'technical_score': round(technical_score, 1),
            'rs_score': round(relative_strength_score, 1),
            'reasoning': reasoning,
            'reasoning_details': self._get_detailed_reasoning(metrics_data),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_fundamental_score(self, metrics: Dict) -> float:
        """
        Calculate fundamental score (0-100) based on EPS growth
        
        Scoring:
        - EPS QoQ growth: 0-25 points
        - EPS YoY growth: 0-25 points
        - EPS trend (last 4 quarters): 0-20 points
        - EPS value (positive/negative): 0-10 points
        """
        score = 0.0
        
        # EPS Quarter over Quarter growth (0-25 points)
        qoq = metrics.get('eps_growth_qoq')
        if qoq is not None:
            if qoq >= 20:
                score += 25
            elif qoq >= 10:
                score += 20
            elif qoq >= 5:
                score += 15
            elif qoq >= 0:
                score += 10
            elif qoq >= -5:
                score += 5
            # Negative growth < -5%: 0 points
        
        # EPS Year over Year growth (0-25 points)
        yoy = metrics.get('eps_growth_yoy')
        if yoy is not None:
            if yoy >= 30:
                score += 25
            elif yoy >= 20:
                score += 20
            elif yoy >= 10:
                score += 15
            elif yoy >= 0:
                score += 10
            elif yoy >= -10:
                score += 5
            # Negative growth < -10%: 0 points
        
        # EPS trend over last 4 quarters (0-20 points)
        eps_history = metrics.get('eps_history')
        if eps_history:
            try:
                eps_data = eps_history if isinstance(eps_history, dict) else {}
                quarters = eps_data.get('latest_quarters', [])
                if len(quarters) >= 3:
                    # Check if EPS is trending upward
                    increasing_count = sum(1 for i in range(1, len(quarters)) if quarters[i] > quarters[i-1])
                    trend_score = (increasing_count / (len(quarters) - 1)) * 20
                    score += trend_score
            except:
                pass
        
        # Latest EPS value (0-10 points)
        latest_eps = metrics.get('latest_quarterly_eps')
        if latest_eps is not None:
            if latest_eps > 2:
                score += 10
            elif latest_eps > 1:
                score += 8
            elif latest_eps > 0.5:
                score += 6
            elif latest_eps > 0:
                score += 4
            # Negative EPS: 0 points
        
        return min(score, 100)
    
    def _calculate_technical_score(self, metrics: Dict) -> float:
        """
        Calculate technical score (0-100) based on EMAs
        
        Scoring:
        - EMA alignment (9>21>50): 0-30 points
        - Price position vs EMAs: 0-25 points
        - Weekly EMA trend: 0-25 points
        - Monthly EMA trend: 0-20 points
        """
        score = 0.0
        
        ema_data = metrics.get('ema_data', {})
        if isinstance(ema_data, str):
            import json
            try:
                ema_data = json.loads(ema_data)
            except:
                ema_data = {}
        
        # Daily EMA alignment (0-30 points)
        d_9 = ema_data.get('D_9EMA')
        d_21 = ema_data.get('D_21EMA')
        d_50 = ema_data.get('D_50EMA')
        
        if d_9 and d_21 and d_50:
            # Perfect bullish alignment: 9 > 21 > 50
            if d_9 > d_21 > d_50:
                score += 30
            # Partial alignment
            elif d_9 > d_21:
                score += 20
            elif d_21 > d_50:
                score += 10
            # Bearish alignment: 9 < 21 < 50
            elif d_9 < d_21 < d_50:
                score += 0
            else:
                score += 5  # Mixed signals
        
        # Current price vs EMAs (0-25 points)
        # Note: We don't have current price in metrics, so we'll use EMA proximity as proxy
        if d_9 and d_21:
            gap = ((d_9 - d_21) / d_21) * 100 if d_21 != 0 else 0
            if gap > 5:
                score += 25  # Strong uptrend
            elif gap > 2:
                score += 20
            elif gap > 0:
                score += 15
            elif gap > -2:
                score += 10
            elif gap > -5:
                score += 5
            # gap < -5: 0 points (downtrend)
        
        # Weekly EMA trend (0-25 points)
        w_9 = ema_data.get('W_9EMA')
        w_21 = ema_data.get('W_21EMA')
        w_50 = ema_data.get('W_50EMA')
        
        if w_9 and w_21 and w_50:
            if w_9 > w_21 > w_50:
                score += 25
            elif w_9 > w_21:
                score += 15
            elif w_21 > w_50:
                score += 10
            else:
                score += 5
        
        # Monthly EMA trend (0-20 points)
        m_9 = ema_data.get('M_9EMA')
        m_21 = ema_data.get('M_21EMA')
        
        if m_9 and m_21:
            if m_9 > m_21:
                score += 20
            else:
                score += 5
        
        return min(score, 100)
    
    def _calculate_rs_score(self, metrics: Dict) -> float:
        """
        Calculate relative strength score (0-100)
        
        Scoring:
        - RS vs SPY: 0-50 points
        - RS vs Sector: 0-50 points
        """
        score = 0.0
        
        # RS vs SPY (0-50 points)
        rs_spy = metrics.get('rs_spy')
        if rs_spy is not None:
            if rs_spy >= 20:
                score += 50
            elif rs_spy >= 10:
                score += 40
            elif rs_spy >= 5:
                score += 30
            elif rs_spy >= 0:
                score += 20
            elif rs_spy >= -5:
                score += 10
            elif rs_spy >= -10:
                score += 5
            # rs_spy < -10: 0 points
        
        # RS vs Sector (0-50 points)
        rs_sector = metrics.get('rs_sector')
        if rs_sector is not None:
            if rs_sector >= 15:
                score += 50
            elif rs_sector >= 8:
                score += 40
            elif rs_sector >= 3:
                score += 30
            elif rs_sector >= 0:
                score += 20
            elif rs_sector >= -5:
                score += 10
            elif rs_sector >= -10:
                score += 5
            # rs_sector < -10: 0 points
        
        return min(score, 100)
    
    def _determine_signal_type(self, score: float) -> str:
        """Determine signal type based on total score"""
        if score >= self.STRONG_BUY_THRESHOLD:
            return "STRONG BUY"
        elif score >= self.BUY_THRESHOLD:
            return "BUY"
        elif score >= self.HOLD_THRESHOLD:
            return "HOLD"
        elif score >= self.SELL_THRESHOLD:
            return "SELL"
        else:
            return "STRONG SELL"
    
    def _calculate_confidence(self, fundamental: float, technical: float, rs: float) -> float:
        """
        Calculate confidence level (0-100) based on agreement between signals
        
        High confidence = All three scores agree (all high or all low)
        Low confidence = Mixed signals
        """
        # Normalize scores to 0-1
        f_norm = fundamental / 100
        t_norm = technical / 100
        r_norm = rs / 100
        
        # Calculate variance (how much they disagree)
        avg = (f_norm + t_norm + r_norm) / 3
        variance = sum((x - avg) ** 2 for x in [f_norm, t_norm, r_norm]) / 3
        
        # Lower variance = higher confidence
        # Variance ranges from 0 (perfect agreement) to ~0.22 (maximum disagreement)
        confidence = (1 - (variance / 0.22)) * 100
        
        return min(max(confidence, 0), 100)
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label"""
        if confidence >= 80:
            return "High"
        elif confidence >= 60:
            return "Medium"
        else:
            return "Low"
    
    def _generate_reasoning(self, signal_type: str, metrics: Dict, 
                          fund_score: float, tech_score: float, rs_score: float) -> str:
        """Generate human-readable reasoning for the signal"""
        reasons = []
        
        # Fundamental reasoning
        qoq = metrics.get('eps_growth_qoq')
        yoy = metrics.get('eps_growth_yoy')
        
        if fund_score >= 70:
            reasons.append(f"Strong fundamentals (EPS growth: QoQ {qoq:+.1f}%, YoY {yoy:+.1f}%)" if qoq and yoy else "Strong fundamentals")
        elif fund_score >= 40:
            reasons.append("Moderate fundamentals")
        else:
            reasons.append(f"Weak fundamentals (EPS declining)" if qoq and qoq < 0 else "Weak fundamentals")
        
        # Technical reasoning
        if tech_score >= 70:
            reasons.append("Bullish technical setup (EMAs aligned)")
        elif tech_score >= 40:
            reasons.append("Mixed technical signals")
        else:
            reasons.append("Bearish technical setup")
        
        # Relative strength reasoning
        rs_spy = metrics.get('rs_spy')
        rs_sector = metrics.get('rs_sector')
        
        if rs_score >= 70:
            reasons.append(f"Outperforming market (SPY {rs_spy:+.1f}%)" if rs_spy else "Outperforming market")
        elif rs_score >= 40:
            reasons.append("Market-relative performance")
        else:
            reasons.append(f"Underperforming market (SPY {rs_spy:+.1f}%)" if rs_spy else "Underperforming market")
        
        return " • ".join(reasons)
    
    def _get_detailed_reasoning(self, metrics: Dict) -> Dict:
        """Get detailed breakdown of all metrics"""
        return {
            'eps_qoq': metrics.get('eps_growth_qoq'),
            'eps_yoy': metrics.get('eps_growth_yoy'),
            'latest_eps': metrics.get('latest_quarterly_eps'),
            'rs_spy': metrics.get('rs_spy'),
            'rs_sector': metrics.get('rs_sector'),
            'has_ema_data': bool(metrics.get('ema_data'))
        }
    
    def generate_signals_for_all_stocks(self, stocks_data: List[Dict]) -> List[Dict]:
        """
        Generate signals for multiple stocks
        
        Args:
            stocks_data: List of dictionaries, each containing 'stock' and 'metrics' keys
            
        Returns:
            List of signal dictionaries, sorted by signal score (descending)
        """
        signals = []
        
        for stock_data in stocks_data:
            try:
                stock = stock_data.get('stock', {})
                metrics = stock_data.get('metrics', {})
                
                signal = self.generate_signal(stock, metrics)
                signals.append(signal)
            except Exception as e:
                print(f"Error generating signal for {stock_data.get('stock', {}).get('symbol', 'UNKNOWN')}: {e}", flush=True)
                continue
        
        # Sort by signal score (highest first)
        signals.sort(key=lambda x: x['signal_score'], reverse=True)
        
        return signals
    
    def get_signal_summary(self, signals: List[Dict]) -> Dict:
        """
        Get summary statistics for all signals
        
        Returns:
            Dictionary with summary statistics
        """
        if not signals:
            return {
                'total_signals': 0,
                'strong_buy_count': 0,
                'buy_count': 0,
                'hold_count': 0,
                'sell_count': 0,
                'strong_sell_count': 0,
                'avg_score': 0,
                'high_confidence_count': 0
            }
        
        signal_counts = {
            'STRONG BUY': 0,
            'BUY': 0,
            'HOLD': 0,
            'SELL': 0,
            'STRONG SELL': 0
        }
        
        high_confidence = 0
        total_score = 0
        
        for signal in signals:
            signal_type = signal.get('signal_type')
            if signal_type in signal_counts:
                signal_counts[signal_type] += 1
            
            if signal.get('confidence_level') == 'High':
                high_confidence += 1
            
            total_score += signal.get('signal_score', 0)
        
        return {
            'total_signals': len(signals),
            'strong_buy_count': signal_counts['STRONG BUY'],
            'buy_count': signal_counts['BUY'],
            'hold_count': signal_counts['HOLD'],
            'sell_count': signal_counts['SELL'],
            'strong_sell_count': signal_counts['STRONG SELL'],
            'avg_score': round(total_score / len(signals), 1) if signals else 0,
            'high_confidence_count': high_confidence
        }

