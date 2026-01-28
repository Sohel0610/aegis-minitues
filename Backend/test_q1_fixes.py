#!/usr/bin/env python3
"""
Test script to verify the Q1 minutes generation fixes.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from chatbot_backend.fastapi_server import replace_placeholders_in_text, Q1MinutesData, Director, Attendee, Signatory, YearRange

def test_authorised_officer_replacement():
    """Test that authorised officer is properly handled."""
    # Create test data with no attendees
    data_no_attendees = Q1MinutesData(
        companyName='Test Company',
        meetingNumber='1st',
        meetingType='Board Meeting',
        meetingDay='Monday',
        meetingDate='2023-06-01',
        timeCommenced='10:00 AM',
        timeConcluded='11:00 AM',
        meetingPlace='Office',
        presentDirectors=[Director(name='John Doe', din='12345678')],
        chairmanName='John Doe',
        inAttendance=[],
        previousMinutesDate='2023-05-01',
        interestDisclosures=[],
        disqualificationDeclarations=[],
        auditorPaymentNumber=50000,
        auditorPaymentWords='Fifty Thousand Only',
        auditorPaymentYear=2023,
        fsYear=2023,
        rptFinYearRange=YearRange(from_year=2022, to_year=2023),
        signatory1=Signatory(name='John Doe', role='Director', din='12345678'),
        signatory2=Signatory(name='Jane Smith', role='Director', din='87654321'),
        directorsReportYear=2023,
        agmNumber='1st',
        agmDayName='Friday',
        agmDay=15,
        agmMonth='June',
        agmYear=2023,
        agmTime='2:00 PM',
        registeredOfficeAddress='123 Main St',
        chairmanShortName='John Doe',
        recordingDate='2023-06-02',
        signingDate='2023-06-02',
        signingPlace='Office',
        signingChairmanName='John Doe',
        authorisedOfficer='Authorised Officer'
    )
    
    # Test with no attendees
    result_no_attendees = replace_placeholders_in_text('In ATTENDANCE: – [Manual]', data_no_attendees)
    print(f"Test with no attendees: {result_no_attendees}")
    assert '[Authorised Officer to be added]' in result_no_attendees
    
    # Create test data with attendees
    data_with_attendees = Q1MinutesData(
        companyName='Test Company',
        meetingNumber='1st',
        meetingType='Board Meeting',
        meetingDay='Monday',
        meetingDate='2023-06-01',
        timeCommenced='10:00 AM',
        timeConcluded='11:00 AM',
        meetingPlace='Office',
        presentDirectors=[Director(name='John Doe', din='12345678')],
        chairmanName='John Doe',
        inAttendance=[Attendee(name='Robert Brown', role='Authorised Officer')],
        previousMinutesDate='2023-05-01',
        interestDisclosures=[],
        disqualificationDeclarations=[],
        auditorPaymentNumber=50000,
        auditorPaymentWords='Fifty Thousand Only',
        auditorPaymentYear=2023,
        fsYear=2023,
        rptFinYearRange=YearRange(from_year=2022, to_year=2023),
        signatory1=Signatory(name='John Doe', role='Director', din='12345678'),
        signatory2=Signatory(name='Jane Smith', role='Director', din='87654321'),
        directorsReportYear=2023,
        agmNumber='1st',
        agmDayName='Friday',
        agmDay=15,
        agmMonth='June',
        agmYear=2023,
        agmTime='2:00 PM',
        registeredOfficeAddress='123 Main St',
        chairmanShortName='John Doe',
        recordingDate='2023-06-02',
        signingDate='2023-06-02',
        signingPlace='Office',
        signingChairmanName='John Doe',
        authorisedOfficer='Robert Brown (Authorised Officer)'
    )
    
    # Test with attendees
    result_with_attendees = replace_placeholders_in_text('In ATTENDANCE: – [Manual]', data_with_attendees)
    print(f"Test with attendees: {result_with_attendees}")
    assert 'Robert Brown (Authorised Officer)' in result_with_attendees
    
    print("All tests passed!")

if __name__ == '__main__':
    test_authorised_officer_replacement()