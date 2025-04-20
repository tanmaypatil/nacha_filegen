import datetime

class NachaGenerator:
    def __init__(self, immediate_destination='071000505', immediate_origin='1234567890',
                 company_name='COMPANY NAME', company_id='1234567890'):
        """
        Initialize NACHA file generator with company information
        
        Args:
            immediate_destination: Bank routing number (default: LaSalle Bank)
            immediate_origin: Company identification number (10 digits)
            company_name: Company name (max 16 chars)
            company_id: Company ID number (10 digits)
        """
        self.immediate_destination = immediate_destination
        self.immediate_origin = immediate_origin
        self.company_name = company_name[:16]  # Truncate to 16 chars if longer
        self.company_id = company_id
        self.batch_number = 1
        self.entry_count = 0
        self.entry_hash = 0
        self.total_debit = 0
        self.total_credit = 0
        self.records = []
        
    def create_file_header(self):
        """Create the File Header Record (Type 1)"""
        today = datetime.datetime.now()
        file_date = today.strftime('%y%m%d')
        file_time = today.strftime('%H%M')
        
        record = '1'  # Record Type Code
        record += '01'  # Priority Code
        record += f" {self.immediate_destination:9}"  # Immediate Destination (leading space + 9 digits)
        record += f"{self.immediate_origin:10}"  # Immediate Origin
        record += file_date  # File Creation Date
        record += file_time  # File Creation Time
        record += 'A'  # File ID Modifier
        record += '094'  # Record Size
        record += '10'  # Blocking Factor
        record += '1'  # Format Code
        record += 'LaSalle Bank N.A.'.ljust(23)  # Immediate Destination Name
        record += self.company_name.ljust(23)  # Immediate Origin Name
        record += ' ' * 8  # Reference Code (8 spaces)
        
        return record.ljust(94)  # Each record must be 94 characters
    
    def create_batch_header(self, service_class_code='200', std_entry_class='PPD', 
                           entry_description='PAYMENT', effective_date=None):
        """Create the Batch Header Record (Type 5)"""
        today = datetime.datetime.now()
        if effective_date is None:
            effective_date = today
            
        descriptive_date = today.strftime('%y%m%d')
        effective_date_str = effective_date.strftime('%y%m%d')
        
        record = '5'  # Record Type Code
        record += service_class_code  # Service Class Code
        record += self.company_name.ljust(16)  # Company Name
        record += ' ' * 20  # Company Discretionary Data
        record += self.company_id.ljust(10)  # Company Identification
        record += std_entry_class  # Standard Entry Class Code
        record += entry_description.ljust(10)  # Company Entry Description
        record += descriptive_date  # Company Descriptive Date
        record += effective_date_str  # Effective Entry Date
        record += ' ' * 3  # Settlement Date (Julian) - Leave blank
        record += '1'  # Originator Status Code
        record += self.immediate_destination  # Originating DFI Identification
        record += str(self.batch_number).zfill(7)  # Batch Number
        
        return record.ljust(94)
    
    def create_entry_detail(self, routing_number, account_number, amount, transaction_type='credit',
                           id_number='', individual_name='', transaction_code=None):
        """
        Create Entry Detail Record (Type 6)
        
        Args:
            routing_number: Receiving bank routing number (9 digits)
            account_number: Receiving account number
            amount: Transaction amount in cents
            transaction_type: 'credit' or 'debit'
            id_number: Identification number (optional)
            individual_name: Receiver's name (optional)
            transaction_code: Override automatic transaction code determination
        """
        # Determine transaction code if not provided
        if transaction_code is None:
            if transaction_type.lower() == 'credit':
                transaction_code = '22'  # Checking Account Credit
            else:
                transaction_code = '27'  # Checking Account Debit
        
        # Calculate entry hash (first 8 digits of routing number)
        routing_first_8 = routing_number[:8]
        self.entry_hash += int(routing_first_8)
        
        # Track totals
        amount_int = int(amount)
        if transaction_type.lower() == 'credit':
            self.total_credit += amount_int
        else:
            self.total_debit += amount_int
            
        self.entry_count += 1
        
        # Format amount with leading zeros
        amount_str = str(amount_int).zfill(10)
        
        record = '6'  # Record Type Code
        record += transaction_code  # Transaction Code
        record += routing_number[:8]  # Receiving DFI Identification
        record += routing_number[8]  # Check Digit
        record += account_number.ljust(17)  # DFI Account Number
        record += amount_str  # Amount
        record += id_number.ljust(15)  # Individual Identification Number
        record += individual_name.ljust(22)  # Individual Name
        record += '  '  # Discretionary Data
        record += '0'  # Addenda Record Indicator
        record += '01234567'.ljust(7)  # Trace Number (will be assigned by bank)
        
        return record.ljust(94)
    
    def create_batch_control(self):
        """Create the Batch Control Record (Type 8)"""
        record = '8'  # Record Type Code
        record += '200'  # Service Class Code
        record += str(self.entry_count).zfill(6)  # Entry/Addenda Count
        record += str(self.entry_hash)[-10:].zfill(10)  # Entry Hash (last 10 digits)
        record += str(self.total_debit).zfill(12)  # Total Debit Entry Dollar Amount
        record += str(self.total_credit).zfill(12)  # Total Credit Entry Dollar Amount
        record += self.company_id.ljust(10)  # Company Identification
        record += ' ' * 19  # Message Authentication Code
        record += ' ' * 6  # Reserved
        record += self.immediate_destination  # Originating DFI Identification
        record += str(self.batch_number).zfill(7)  # Batch Number
        
        return record.ljust(94)
    
    def create_file_control(self):
        """Create the File Control Record (Type 9)"""
        record = '9'  # Record Type Code
        record += '000001'.ljust(6)  # Batch Count
        record += '000003'.ljust(6)  # Block Count - typically File Header + File Control + 1 for each batch
        record += str(self.entry_count).zfill(8)  # Entry/Addenda Count
        record += str(self.entry_hash)[-10:].zfill(10)  # Entry Hash
        record += str(self.total_debit).zfill(12)  # Total Debit Entry Dollar Amount in File
        record += str(self.total_credit).zfill(12)  # Total Credit Entry Dollar Amount in File
        record += ' ' * 39  # Reserved
        
        return record.ljust(94)
    
    def generate_file(self, transactions):
        """
        Generate a complete NACHA file with the given transactions
        
        Args:
            transactions: List of dictionaries containing transaction details
                          Each dict should have: routing_number, account_number, amount, 
                          transaction_type, id_number (optional), and name (optional)
        
        Returns:
            Complete NACHA file as a string
        """
        # Reset totals
        self.entry_count = 0
        self.entry_hash = 0
        self.total_debit = 0
        self.total_credit = 0
        self.records = []
        
        # Add file header
        self.records.append(self.create_file_header())
        
        # Add batch header
        self.records.append(self.create_batch_header())
        
        # Add transactions
        for txn in transactions:
            self.records.append(
                self.create_entry_detail(
                    routing_number=txn['routing_number'],
                    account_number=txn['account_number'],
                    amount=txn['amount'],
                    transaction_type=txn['transaction_type'],
                    id_number=txn.get('id_number', ''),
                    individual_name=txn.get('name', '')
                )
            )
        
        # Add batch control
        self.records.append(self.create_batch_control())
        
        # Add file control
        self.records.append(self.create_file_control())
        
        # Return file as string
        return '\n'.join(self.records)

# Example usage
if __name__ == '__main__':
    # Initialize NACHA generator
    nacha = NachaGenerator(
        immediate_origin='1234567890',
        company_name='ACME CORP',
        company_id='1234567890'
    )
    
    # Define two transactions
    transactions = [
        {
            'routing_number': '123456789',
            'account_number': '9876543210',
            'amount': 100000,  # $1,000.00 (in cents)
            'transaction_type': 'credit',
            'id_number': 'EMP001',
            'name': 'JOHN DOE'
        },
        {
            'routing_number': '987654321',
            'account_number': '1234567890',
            'amount': 250000,  # $2,500.00 (in cents)
            'transaction_type': 'credit',
            'id_number': 'EMP002',
            'name': 'JANE SMITH'
        }
    ]
    
    # Generate NACHA file
    nacha_file = nacha.generate_file(transactions)
    
    # Print or save to file
    print(nacha_file)
    
    # Optionally save to file
    with open('nacha_payment_file.txt', 'w') as f:
        f.write(nacha_file)