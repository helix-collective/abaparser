"""
Parse an ABA file, into something useable

I've used http://www.cemtexaba.com/aba-format/cemtex-aba-file-format-details.html as
the file format reference
"""

class Tokenizer(object):
    def __init__(self, line):
        self.line = line
        self.curpos = 0

    def next_chunk(self, nchars):
        chunk = self.line[self.curpos:self.curpos+nchars]
        self.curpos += nchars
        return chunk

    def next_str(self, nchars):
        return self.next_chunk(nchars).strip()

    def next_int(self, nchars):
        return int(self.next_chunk(nchars).strip())

    def assert_chunk(self, nchars, expected, field_name):
        chunk = self.next_chunk(nchars)
        if chunk != expected:
            raise AssertionError('%r != %r (for field %s)' % (chunk, expected, field_name))

    def skip_padding(self, nchars):
        self.assert_chunk(nchars, ' ' * nchars, 'padding')

    def assert_empty(self):
        rest = self.line[self.curpos:]
        if rest not in ['', '\r\n', '\n']:
            raise AssertionError('Unconsumed data in tokenizer %r', rest)

def parse_desc(tokens):
    """
        >>> parse_desc(Tokenizer("0                 01BWA       Helix Collective          000000Payroll31Mar310315                                        "))
        {'FinancialInstitutionName': 'BWA', 'ProcessDate': '310315', 'ApcaNumber': 0, 'GeneratedBy': 'Helix Collective', 'EntriesDescription': 'Payroll31Mar'}
        
    """
    entry = {'type': 'description'}

    tokens.assert_chunk(1, '0', 'record type')
    tokens.skip_padding(17)
    tokens.next_chunk(2) # Real Sequence number
    entry['FinancialInstitutionName'] = tokens.next_str(3)
    tokens.skip_padding(7)
    entry['GeneratedBy'] = tokens.next_str(26)
    entry['ApcaNumber'] = tokens.next_int(6)
    entry['EntriesDescription'] = tokens.next_str(12)
    entry['ProcessDate'] = tokens.next_str(6)
    tokens.skip_padding(40)
    tokens.assert_empty()

    return entry

def parse_detail(tokens):
    """
        >>> parse_detail(Tokenizer("1082-406598209326 530000466867Timothy Cerexhe                 Paycheck          302-973  0307047Helix Collective00000000"))
        {'Indicator': '', 'AccountNumber': '598209326', 'FromAccountName': 'Helix Collective', 'LodgementReference': 'Paycheck', 'AccountName': 'Timothy Cerexhe', 'TransactionCode': 53, 'Amount': 466867, 'WithholdingTax': 0, 'FromBsb': '302-973', 'FromAccountNumber': '0307047', 'Bsb': '082-406'}
        
    """
    entry = {'type': 'detail'}

    tokens.assert_chunk(1, '1', 'record type')
    entry['Bsb'] = tokens.next_str(7)
    entry['AccountNumber'] = tokens.next_str(9)
    entry['Indicator'] = tokens.next_str(1)
    entry['TransactionCode'] = tokens.next_int(2)
    entry['Amount'] = tokens.next_int(10)
    entry['AccountName'] = tokens.next_str(32)
    entry['LodgementReference'] = tokens.next_str(18)
    entry['FromBsb'] = tokens.next_str(7)
    entry['FromAccountNumber'] = tokens.next_str(9)
    entry['FromAccountName'] = tokens.next_str(16)
    entry['WithholdingTax'] = tokens.next_int(8)
    tokens.assert_empty()

    # Indicator validation.
    indicator = entry['Indicator']
    withholding_tax = entry['WithholdingTax']
    if indicator == '' or indicator.upper() == 'N':
        # TODO: Verify that the '== N' check above is correct
        assert(withholding_tax == 0)
    else:
        # TODO: Verify that these assertions are correct, in the situation where
        # there is a tax withholding
        assert(indicator.upper() in "WXY")
        assert(withholding_tax > 0)

    #TransactionCode validation
    transaction_code = entry['TransactionCode']
    valid_codes = [
        13, # Externally initiated debit items
        50, # Externally initiated credit items with the exception of those bearing Transaction Codes
        51, # Australian Government Security Interest
        52, # Family Allowance
        53, # Pay
        54, # Pension
        55, # Allotment
        56, # Dividend
        57, # Debenture/Note Interest
    ]
    assert(transaction_code in valid_codes)

    return entry

def parse_total(tokens):
    """
        >>> parse_total(Tokenizer("7999-999            000000000000004668670000466867                        000002                                        "))
        {'CreditTotalAmount': 466867, 'NetTotalAmount': 0, 'DebitTotalAmount': 466867, 'NumTypeOneRecords': 2}
    """
    entry = {'type': 'total'}

    tokens.assert_chunk(1, '7', 'record type')
    tokens.assert_chunk(7, '999-999', 'bsb')
    tokens.skip_padding(12)
    entry['NetTotalAmount'] = tokens.next_int(10)
    entry['CreditTotalAmount'] = tokens.next_int(10)
    entry['DebitTotalAmount'] = tokens.next_int(10)
    tokens.skip_padding(24)
    entry['NumTypeOneRecords'] = tokens.next_int(6)
    tokens.skip_padding(40)
    tokens.assert_empty()

    return entry

def parse(lines):
    for l in lines:
        if l[0] == '0':
            yield parse_desc(Tokenizer(l))
        elif l[0] == '1':
            yield parse_detail(Tokenizer(l))
        elif l[0] == '7':
            yield parse_total(Tokenizer(l))

if __name__ == '__main__':
    import sys
    for entry in parse(sys.stdin.readlines()):
        if entry['type'] == 'description':
            print entry['EntriesDescription']


        if entry['type'] == 'detail' and entry['TransactionCode'] != 13:
            print '\t'.join([entry['Bsb'], entry['AccountNumber'], entry['AccountName'], entry['LodgementReference'], "%.2f" % (entry['Amount'] / 100.0)])
