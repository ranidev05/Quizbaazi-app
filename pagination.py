# pagination.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class InlineKeyboardPaginator:
    """Helper class for paginating inline keyboards"""
    
    def __init__(self, items, items_per_page=5, current_page=1):
        self.items = items
        self.items_per_page = items_per_page
        self.current_page = current_page
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    def get_page_items(self):
        """Get items for the current page"""
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.items[start_idx:end_idx]
    
    def add_navigation_buttons(self, keyboard):
        """Add navigation buttons to the keyboard"""
        nav_buttons = []
        
        # Only add previous button if not on first page
        if self.current_page > 1:
            nav_buttons.append(InlineKeyboardButton(
                "◀️ Previous", callback_data=f"page_{self.current_page - 1}"
            ))
        
        # Page indicator
        nav_buttons.append(InlineKeyboardButton(
            f"Page {self.current_page}/{self.total_pages}", callback_data="page_info"
        ))
        
        # Only add next button if not on last page
        if self.current_page < self.total_pages:
            nav_buttons.append(InlineKeyboardButton(
                "Next ▶️", callback_data=f"page_{self.current_page + 1}"
            ))
        
        keyboard.append(nav_buttons)
        return keyboard
