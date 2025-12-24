from typing import Dict, Optional
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchStatsScraper(BaseSofascoreScraper):
    """Scraper for fetching detailed match statistics."""
    
    def get_match_statistics(self, match_id: int) -> Dict:
        """
        Get comprehensive statistics for a match (First Half + Second Half).
        Returns structured data for both halves.
        """
        endpoint = f"/event/{match_id}/statistics"
        
        logger.info(f"Fetching statistics for match {match_id}")
        data = self._make_request(endpoint)
        
        if not data or 'statistics' not in data:
            logger.error(f"No statistics found for match {match_id}")
            return None
        
        stats_by_period = {}
        
        for period in data['statistics']:
            period_name = period.get('period')
            
            # Only collect 1ST and 2ND half
            if period_name in ['1ST', '2ND']:
                stats_by_period[period_name] = self._parse_period_stats(period)
        
        return {
            'match_id': match_id,
            'first_half': stats_by_period.get('1ST', {}),
            'second_half': stats_by_period.get('2ND', {})
        }
    
    def _parse_period_stats(self, period: Dict) -> Dict:
        """Parse statistics for a specific period."""
        period_stats = {}
        
        for group in period.get('groups', []):
            group_name = group.get('groupName')
            
            for stat_item in group.get('statisticsItems', []):
                stat_name = stat_item.get('name')
                home_value = stat_item.get('home')
                away_value = stat_item.get('away')
                
                # Store both home and away values
                period_stats[f"{stat_name}_home"] = home_value
                period_stats[f"{stat_name}_away"] = away_value
        
        return period_stats
    
    def display_match_statistics(self, stats_data: Dict):
        """Display match statistics in clean format."""
        if not stats_data:
            print("❌ No statistics available")
            return
        
        match_id = stats_data['match_id']
        first_half = stats_data.get('first_half', {})
        second_half = stats_data.get('second_half', {})
        
        print("\n" + "="*80)
        print(f"📊 MATCH STATISTICS")
        print(f"Match ID: {match_id}")
        print("="*80)
        
        if not first_half and not second_half:
            print("❌ No statistics found for either half")
            return
        
        # Display First Half
        if first_half:
            print("\n🔵 FIRST HALF STATISTICS:")
            print("-" * 80)
            self._display_period_stats(first_half)
        
        # Display Second Half
        if second_half:
            print("\n🔴 SECOND HALF STATISTICS:")
            print("-" * 80)
            self._display_period_stats(second_half)
    
    def _display_period_stats(self, period_stats: Dict):
        """Display statistics for one period."""
        if not period_stats:
            print("  No data available")
            return
        
        # Get unique stat names (without _home/_away suffix)
        stat_names = set()
        for key in period_stats.keys():
            if key.endswith('_home') or key.endswith('_away'):
                stat_name = key.rsplit('_', 1)[0]
                stat_names.add(stat_name)
        
        # Display each stat with home and away values
        for stat_name in sorted(stat_names):
            home_key = f"{stat_name}_home"
            away_key = f"{stat_name}_away"
            
            home_val = period_stats.get(home_key, 'N/A')
            away_val = period_stats.get(away_key, 'N/A')
            
            # Format the stat name for display
            display_name = stat_name.replace('_', ' ').title()
            
            print(f"  {display_name:30s} | Home: {home_val:>6} | Away: {away_val:>6}")


def test_newcastle_leverkusen():
    """Test with Newcastle vs Leverkusen match."""
    scraper = MatchStatsScraper()
    
    match_id = 14566707  # Newcastle vs Leverkusen
    
    print("\n" + "🔍 MATCH STATISTICS SCRAPER TEST".center(80))
    print("="*80)
    print(f"Match: Bayer 04 Leverkusen vs Newcastle United")
    print(f"Match ID: {match_id}")
    print("="*80)
    
    stats = scraper.get_match_statistics(match_id)
    scraper.display_match_statistics(stats)
    
    print("\n" + "="*80)
    print("✅ Statistics scraper test complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_newcastle_leverkusen()
