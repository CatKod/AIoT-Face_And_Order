import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config
from database_manager import DatabaseManager

class RecommendationEngine:
    """Generates personalized food and drink recommendations for customers."""
    
    def __init__(self):
        self.db = DatabaseManager()
        
    def get_customer_recommendations(self, customer_id: int, limit: int = 5) -> List[Dict]:
        """Generate personalized recommendations for a customer."""
        # Get customer's order history
        order_history = self.db.get_customer_order_history(customer_id)
        
        if len(order_history) < config.MIN_ORDERS_FOR_RECOMMENDATION:
            # New customer - recommend popular items
            return self._get_popular_recommendations(limit)
        
        # Get frequency-based recommendations
        frequency_recommendations = self._get_frequency_based_recommendations(customer_id, limit * 2)
        
        # Get similarity-based recommendations
        similarity_recommendations = self._get_similarity_based_recommendations(customer_id, limit * 2)
        
        # Get recency-based recommendations
        recency_recommendations = self._get_recency_based_recommendations(customer_id, limit * 2)
        
        # Combine and score recommendations
        combined_recommendations = self._combine_recommendations(
            frequency_recommendations,
            similarity_recommendations,
            recency_recommendations,
            limit
        )
        
        return combined_recommendations
    
    def _get_frequency_based_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Recommend items based on customer's order frequency."""
        order_history = self.db.get_customer_order_history(customer_id)
        
        # Count item frequencies
        item_counts = Counter()
        for order in order_history:
            for item in order['items']:
                item_counts[item['menu_item_id']] += item['quantity']
        
        # Get most frequent items
        most_frequent = item_counts.most_common(limit)
        
        recommendations = []
        for menu_item_id, count in most_frequent:
            # Get menu item details
            menu_items = self.db.get_menu_items()
            item_details = next((item for item in menu_items if item['id'] == menu_item_id), None)
            
            if item_details:
                recommendations.append({
                    'item': item_details,
                    'score': count,
                    'reason': f"You've ordered this {count} times",
                    'recommendation_type': 'frequency'
                })
        
        return recommendations
    
    def _get_similarity_based_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Recommend items similar to what the customer has ordered."""
        order_history = self.db.get_customer_order_history(customer_id)
        all_menu_items = self.db.get_menu_items()
        
        # Get customer's ordered items
        ordered_items = set()
        for order in order_history:
            for item in order['items']:
                ordered_items.add(item['menu_item_id'])
        
        if not ordered_items:
            return []
        
        # Create feature vectors for menu items (based on category, subcategory, ingredients)
        item_features = []
        item_ids = []
        
        for item in all_menu_items:
            features = []
            features.append(item['category'])
            if item['subcategory']:
                features.append(item['subcategory'])
            if item['ingredients']:
                features.extend(item['ingredients'])
            
            item_features.append(' '.join(features))
            item_ids.append(item['id'])
        
        # Calculate TF-IDF similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(item_features)
        
        recommendations = []
        
        # For each ordered item, find similar items
        for ordered_item_id in ordered_items:
            if ordered_item_id in item_ids:
                ordered_item_index = item_ids.index(ordered_item_id)
                similarities = cosine_similarity(tfidf_matrix[ordered_item_index:ordered_item_index+1], tfidf_matrix).flatten()
                
                # Get top similar items (excluding the item itself)
                similar_indices = similarities.argsort()[-limit-1:-1][::-1]
                
                for idx in similar_indices:
                    similar_item_id = item_ids[idx]
                    if similar_item_id not in ordered_items:  # Don't recommend already ordered items
                        item_details = all_menu_items[idx]
                        recommendations.append({
                            'item': item_details,
                            'score': similarities[idx],
                            'reason': f"Similar to items you've enjoyed",
                            'recommendation_type': 'similarity'
                        })
        
        # Remove duplicates and sort by score
        seen_items = set()
        unique_recommendations = []
        for rec in sorted(recommendations, key=lambda x: x['score'], reverse=True):
            if rec['item']['id'] not in seen_items:
                seen_items.add(rec['item']['id'])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    def _get_recency_based_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Recommend items based on recent ordering patterns."""
        # Get recent orders (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        order_history = self.db.get_customer_order_history(customer_id)
        
        recent_orders = [
            order for order in order_history 
            if datetime.fromisoformat(order['order_date'].replace('Z', '+00:00')) > recent_date
        ]
        
        # Count items from recent orders
        recent_item_counts = Counter()
        for order in recent_orders:
            for item in order['items']:
                recent_item_counts[item['menu_item_id']] += item['quantity']
        
        recommendations = []
        for menu_item_id, count in recent_item_counts.most_common(limit):
            menu_items = self.db.get_menu_items()
            item_details = next((item for item in menu_items if item['id'] == menu_item_id), None)
            
            if item_details:
                recommendations.append({
                    'item': item_details,
                    'score': count,
                    'reason': f"Recently ordered {count} times",
                    'recommendation_type': 'recency'
                })
        
        return recommendations
    
    def _get_popular_recommendations(self, limit: int) -> List[Dict]:
        """Get popular menu items for new customers."""
        popular_items = self.db.get_popular_items(limit)
        
        recommendations = []
        for item in popular_items:
            recommendations.append({
                'item': item,
                'score': item.get('order_count', 0),
                'reason': "Popular choice among customers",
                'recommendation_type': 'popular'
            })
        
        return recommendations
    
    def _combine_recommendations(self, frequency_recs: List[Dict], 
                               similarity_recs: List[Dict], 
                               recency_recs: List[Dict], 
                               limit: int) -> List[Dict]:
        """Combine different recommendation types with weighted scoring."""
        
        # Create a dictionary to combine scores for the same items
        combined_scores = {}
        
        # Process frequency recommendations
        for rec in frequency_recs:
            item_id = rec['item']['id']
            if item_id not in combined_scores:
                combined_scores[item_id] = {
                    'item': rec['item'],
                    'total_score': 0,
                    'reasons': [],
                    'types': set()
                }
            
            combined_scores[item_id]['total_score'] += rec['score'] * config.RECOMMENDATION_WEIGHT_FREQUENCY
            combined_scores[item_id]['reasons'].append(rec['reason'])
            combined_scores[item_id]['types'].add(rec['recommendation_type'])
        
        # Process similarity recommendations
        for rec in similarity_recs:
            item_id = rec['item']['id']
            if item_id not in combined_scores:
                combined_scores[item_id] = {
                    'item': rec['item'],
                    'total_score': 0,
                    'reasons': [],
                    'types': set()
                }
            
            combined_scores[item_id]['total_score'] += rec['score'] * config.RECOMMENDATION_WEIGHT_SIMILARITY
            combined_scores[item_id]['reasons'].append(rec['reason'])
            combined_scores[item_id]['types'].add(rec['recommendation_type'])
        
        # Process recency recommendations
        for rec in recency_recs:
            item_id = rec['item']['id']
            if item_id not in combined_scores:
                combined_scores[item_id] = {
                    'item': rec['item'],
                    'total_score': 0,
                    'reasons': [],
                    'types': set()
                }
            
            combined_scores[item_id]['total_score'] += rec['score'] * config.RECOMMENDATION_WEIGHT_RECENCY
            combined_scores[item_id]['reasons'].append(rec['reason'])
            combined_scores[item_id]['types'].add(rec['recommendation_type'])
        
        # Sort by total score and return top recommendations
        final_recommendations = []
        for item_id, data in sorted(combined_scores.items(), 
                                  key=lambda x: x[1]['total_score'], 
                                  reverse=True)[:limit]:
            
            # Combine reasons intelligently
            unique_reasons = list(set(data['reasons']))
            combined_reason = "; ".join(unique_reasons[:2])  # Limit to 2 reasons for readability
            
            final_recommendations.append({
                'item': data['item'],
                'score': data['total_score'],
                'reason': combined_reason,
                'recommendation_types': list(data['types'])
            })
        
        return final_recommendations
    
    def get_complementary_items(self, item_ids: List[int], limit: int = 3) -> List[Dict]:
        """Get items that are commonly ordered together with given items."""
        # This would require analyzing order patterns to find items frequently ordered together
        # For now, return simple category-based complementary items
        
        menu_items = self.db.get_menu_items()
        given_items = [item for item in menu_items if item['id'] in item_ids]
        
        complementary = []
        
        for given_item in given_items:
            if given_item['category'] == 'drink' and given_item['subcategory'] == 'coffee':
                # Recommend pastries with coffee
                pastries = [item for item in menu_items 
                          if item['category'] == 'food' and item['subcategory'] == 'pastry']
                complementary.extend(pastries[:2])
            
            elif given_item['category'] == 'food' and given_item['subcategory'] in ['sandwich', 'salad']:
                # Recommend drinks with food
                drinks = [item for item in menu_items 
                        if item['category'] == 'drink']
                complementary.extend(drinks[:2])
        
        # Remove duplicates and return
        seen = set()
        unique_complementary = []
        for item in complementary:
            if item['id'] not in seen and item['id'] not in item_ids:
                seen.add(item['id'])
                unique_complementary.append({
                    'item': item,
                    'reason': "Great combination with your selection",
                    'recommendation_type': 'complementary'
                })
                if len(unique_complementary) >= limit:
                    break
        
        return unique_complementary
