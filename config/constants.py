TRANSACTION_TYPES = ['Expense', 'Income']

CATEGORIES = {
    'Expense': {
        'Food': ['Groceries', 'Dining Out', 'Snacks', 'Coffee', 'Food Delivery'],
        'Transportation': ['Fuel', 'Public Transport', 'Maintenance', 'Parking', 'Ride Share'],
        'Housing': ['Rent', 'Utilities', 'Maintenance', 'Insurance', 'Property Tax'],
        'Entertainment': ['Movies', 'Games', 'Sports', 'Streaming Services', 'Hobbies'],
        'Shopping': ['Clothes', 'Electronics', 'Home Items', 'Gifts', 'Personal Care'],
        'Healthcare': ['Medicine', 'Doctor Visits', 'Insurance', 'Lab Tests', 'Dental'],
        'Bills': ['Credit Card', 'Internet', 'Phone', 'Subscriptions', 'EMI'],
        'Academic': ['Tuition', 'Books', 'Supplies', 'Online Courses', 'Software',  'Others'],
        'Personal': ['Grooming', 'Gym', 'Clothing', 'Accessories', 'Salon', 'Others'],
        'Travel': ['Flights', 'Hotels', 'Sightseeing', 'Travel Insurance', 'Visa'],
        'Investment': ['Stocks', 'Mutual Funds', 'Fixed Deposits', 'Cryptocurrency', 'Gold'],
        'Others': ['Miscellaneous', 'Donations', 'Gifts Given']
    },
    'Income': {
        'Salary': ['Regular', 'Bonus', 'Overtime', 'Allowances', 'Reimbursements'],
        'Investments': ['Dividends', 'Interest', 'Capital Gains', 'Rental Income', 'Crypto'],
        'Freelance': ['Consulting', 'Project Work', 'Commissions', 'Tutoring', 'Content Creation'],
        'Gifts': ['Personal', 'Professional', 'Awards', 'Inheritance'],
        'Academic': ['Scholarships', 'Grants', 'Research Stipend', 'Teaching Assistant', 'Others'],
        'Business': ['Sales', 'Services', 'Commissions', 'Royalties'],
        'Others': ['Miscellaneous', 'Refunds', 'Cashback']
    }
}