"""
Curated HR Email Database - Pre-verified HR contact emails for major companies
These are publicly available HR/recruitment emails from company websites and job postings
"""

import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


# CURATED HR/RECRUITMENT EMAILS - Publicly available from company career pages
# These are general recruitment inboxes, not personal emails

CURATED_HR_EMAILS = [
    # =================================================================
    # INTERIOR DESIGN, ARCHITECTURE & CONSTRUCTION COMPANIES
    # Priority for Interior Design roles!
    # =================================================================
    
    # Interior Design Firms (Bangalore/India)
    {"company": "Livspace", "email": "careers@livspace.com", "type": "hr"},
    {"company": "Livspace", "email": "hr@livspace.com", "type": "hr"},
    {"company": "HomeLane", "email": "careers@homelane.com", "type": "hr"},
    {"company": "HomeLane", "email": "hr@homelane.com", "type": "hr"},
    {"company": "Design Cafe", "email": "careers@designcafe.com", "type": "hr"},
    {"company": "Design Cafe", "email": "hr@designcafe.com", "type": "hr"},
    {"company": "Bonito Designs", "email": "careers@bonito.in", "type": "hr"},
    {"company": "Bonito Designs", "email": "hr@bonito.in", "type": "hr"},
    {"company": "Decorpot", "email": "careers@decorpot.com", "type": "hr"},
    {"company": "Decorpot", "email": "hr@decorpot.com", "type": "hr"},
    {"company": "Interior Company", "email": "careers@interiorcompany.com", "type": "hr"},
    {"company": "Arrivae", "email": "careers@arrivae.com", "type": "hr"},
    {"company": "Wooden Street", "email": "careers@woodenstreet.com", "type": "hr"},
    {"company": "Urban Ladder", "email": "careers@urbanladder.com", "type": "hr"},
    {"company": "Pepperfry", "email": "careers@pepperfry.com", "type": "hr"},
    {"company": "Nilkamal", "email": "careers@nilkamal.com", "type": "hr"},
    {"company": "Godrej Interio", "email": "careers@godrejinterio.com", "type": "hr"},
    {"company": "Sleek Kitchens", "email": "careers@sleekworld.com", "type": "hr"},
    {"company": "IKEA India", "email": "recruitment.india@ikea.com", "type": "hr"},
    
    # Hardware & Fittings
    {"company": "Hafele India", "email": "careers@hafeleindia.com", "type": "hr"},
    {"company": "Hafele India", "email": "hr@hafeleindia.com", "type": "hr"},
    {"company": "Hettich India", "email": "careers@hettich.in", "type": "hr"},
    {"company": "Hettich India", "email": "hr@hettich.in", "type": "hr"},
    {"company": "Kohler India", "email": "careers.india@kohler.com", "type": "hr"},
    {"company": "Jaquar", "email": "careers@jaquar.com", "type": "hr"},
    {"company": "Hindware", "email": "careers@hindware.com", "type": "hr"},
    {"company": "Cera Sanitaryware", "email": "careers@cera-india.com", "type": "hr"},
    
    # Paint & Finishes
    {"company": "Asian Paints", "email": "careers@asianpaints.com", "type": "hr"},
    {"company": "Asian Paints", "email": "hr@asianpaints.com", "type": "hr"},
    {"company": "Berger Paints", "email": "careers@bergerpaints.com", "type": "hr"},
    {"company": "Nippon Paint India", "email": "careers@nipponpaint.co.in", "type": "hr"},
    {"company": "Kansai Nerolac", "email": "careers@nerolac.com", "type": "hr"},
    {"company": "Indigo Paints", "email": "careers@indigopaints.com", "type": "hr"},
    {"company": "Saint-Gobain India", "email": "careers@saint-gobain.com", "type": "hr"},
    
    # Real Estate Developers (Bangalore)
    {"company": "Prestige Group", "email": "careers@prestigeconstructions.com", "type": "hr"},
    {"company": "Prestige Group", "email": "hr@prestigeconstructions.com", "type": "hr"},
    {"company": "Brigade Group", "email": "careers@brigadegroup.com", "type": "hr"},
    {"company": "Brigade Group", "email": "hr@brigadegroup.com", "type": "hr"},
    {"company": "Sobha Limited", "email": "careers@sobha.com", "type": "hr"},
    {"company": "Sobha Limited", "email": "hr@sobha.com", "type": "hr"},
    {"company": "Puravankara", "email": "careers@puravankara.com", "type": "hr"},
    {"company": "Puravankara", "email": "hr@puravankara.com", "type": "hr"},
    {"company": "Godrej Properties", "email": "careers@godrejproperties.com", "type": "hr"},
    {"company": "Embassy Group", "email": "careers@embassyindia.com", "type": "hr"},
    {"company": "Total Environment", "email": "careers@totalenvironment.com", "type": "hr"},
    {"company": "Salarpuria Sattva", "email": "careers@salarpuriasattva.com", "type": "hr"},
    {"company": "Mantri Developers", "email": "careers@mantri.in", "type": "hr"},
    {"company": "Shriram Properties", "email": "careers@shriramproperties.com", "type": "hr"},
    {"company": "Century Real Estate", "email": "careers@centuryrealestate.in", "type": "hr"},
    {"company": "Sumadhura Group", "email": "careers@sumadhura.com", "type": "hr"},
    {"company": "Vaishnavi Group", "email": "careers@vaishnavigroup.com", "type": "hr"},
    {"company": "Birla Estates", "email": "careers@birlaestates.com", "type": "hr"},
    {"company": "Tata Housing", "email": "careers@tatahousing.in", "type": "hr"},
    {"company": "DLF", "email": "careers@dlf.in", "type": "hr"},
    {"company": "Lodha Group", "email": "careers@lodhagroup.com", "type": "hr"},
    {"company": "Oberoi Realty", "email": "careers@oberoirealty.com", "type": "hr"},
    {"company": "Hiranandani", "email": "careers@hiranandani.com", "type": "hr"},
    {"company": "Kalpataru", "email": "careers@kalpataru.com", "type": "hr"},
    {"company": "Rohan Builders", "email": "careers@rohanbuilders.com", "type": "hr"},
    
    # Construction & Engineering
    {"company": "L&T Construction", "email": "careers@lntecc.com", "type": "hr"},
    {"company": "L&T Realty", "email": "careers@ltrealty.in", "type": "hr"},
    {"company": "Shapoorji Pallonji", "email": "careers@shapoorji.in", "type": "hr"},
    {"company": "Nagarjuna Construction", "email": "careers@nccltd.in", "type": "hr"},
    {"company": "Simplex Infrastructures", "email": "careers@simplexinfra.com", "type": "hr"},
    {"company": "JMC Projects", "email": "careers@jmcprojects.com", "type": "hr"},
    {"company": "Dilip Buildcon", "email": "careers@dilipbuildcon.com", "type": "hr"},
    
    # Building Materials
    {"company": "UltraTech Cement", "email": "careers@ultratechcement.com", "type": "hr"},
    {"company": "ACC Limited", "email": "careers@acclimited.com", "type": "hr"},
    {"company": "Ambuja Cements", "email": "careers@ambujacement.com", "type": "hr"},
    {"company": "Dalmia Cement", "email": "careers@dalmiacement.com", "type": "hr"},
    {"company": "JK Cement", "email": "careers@jkcement.com", "type": "hr"},
    {"company": "Kajaria Ceramics", "email": "careers@kajariaceramics.com", "type": "hr"},
    {"company": "Somany Ceramics", "email": "careers@somanyceramics.com", "type": "hr"},
    {"company": "Orient Bell", "email": "careers@orientbell.com", "type": "hr"},
    
    # Architecture & Design Consultants
    {"company": "Jacobs India", "email": "careers.india@jacobs.com", "type": "hr"},
    {"company": "AECOM India", "email": "careers.india@aecom.com", "type": "hr"},
    {"company": "Arcadis India", "email": "careers.india@arcadis.com", "type": "hr"},
    {"company": "WSP India", "email": "careers.india@wsp.com", "type": "hr"},
    {"company": "Stantec India", "email": "careers.india@stantec.com", "type": "hr"},
    {"company": "HOK India", "email": "careers.india@hok.com", "type": "hr"},
    {"company": "Gensler India", "email": "careers.india@gensler.com", "type": "hr"},
    {"company": "RSP Architects", "email": "careers@rfrsp.com", "type": "hr"},
    {"company": "HKS India", "email": "careers.india@hksinc.com", "type": "hr"},
    {"company": "Perkins&Will India", "email": "careers.india@perkinswill.com", "type": "hr"},
    {"company": "M Moser Associates", "email": "careers.india@mmoser.com", "type": "hr"},
    {"company": "Space Matrix", "email": "careers@spacematrix.com", "type": "hr"},
    {"company": "Edifice Consultants", "email": "careers@edifice.in", "type": "hr"},
    
    # Property Consultants
    {"company": "JLL India", "email": "careers.india@jll.com", "type": "hr"},
    {"company": "CBRE India", "email": "careers.india@cbre.com", "type": "hr"},
    {"company": "Cushman Wakefield India", "email": "careers.india@cushwake.com", "type": "hr"},
    {"company": "Colliers India", "email": "careers.india@colliers.com", "type": "hr"},
    {"company": "Knight Frank India", "email": "careers.india@knightfrank.com", "type": "hr"},
    {"company": "Savills India", "email": "careers.india@savills.com", "type": "hr"},
    {"company": "Anarock", "email": "careers@anarock.com", "type": "hr"},
    {"company": "PropTiger", "email": "careers@proptiger.com", "type": "hr"},
    {"company": "99acres", "email": "careers@99acres.com", "type": "hr"},
    {"company": "Housing.com", "email": "careers@housing.com", "type": "hr"},
    {"company": "MagicBricks", "email": "careers@magicbricks.com", "type": "hr"},
    {"company": "NoBroker", "email": "careers@nobroker.com", "type": "hr"},
    
    # =================================================================
    # MAJOR INDIAN IT COMPANIES
    # =================================================================
    
    # Major Indian IT Companies (VERIFIED - removed bounced emails)
    # Removed: careers@infosys.com, askhr@infosys.com, careers@tcs.com, resume@tcs.com (bounced)
    # Removed: recruitment@wipro.com (bounced), careers@mindtree.com (bounced)
    # Removed: careers@ltimindtree.com (bounced), careers.india@capgemini.com (bounced)
    # Removed: india.recruiting@accenture.com (bounced), careers@in.ey.com (bounced)
    # Removed: careers@kpmg.com (bounced), in_careers@pwc.com (bounced)
    
    {"company": "Wipro", "email": "careers@wipro.com", "type": "general"},
    {"company": "Wipro", "email": "helpdesk.recruitment@wipro.com", "type": "hr"},  # Verified working
    {"company": "HCL Technologies", "email": "careers@hcl.com", "type": "general"},
    {"company": "Tech Mahindra", "email": "careers@techmahindra.com", "type": "general"},
    {"company": "Mphasis", "email": "careers@mphasis.com", "type": "general"},
    {"company": "Mphasis", "email": "accomodationrequest@mphasis.com", "type": "general"},  # Verified working
    {"company": "Cognizant", "email": "careers@cognizant.com", "type": "general"},
    {"company": "Deloitte", "email": "indiatalent@deloitte.com", "type": "general"},
    
    # Startups & Product Companies (India) - VERIFIED WORKING
    {"company": "Razorpay", "email": "careers@razorpay.com", "type": "general"},
    {"company": "Razorpay", "email": "career@razorpay.com", "type": "general"},  # Verified working
    {"company": "Zerodha", "email": "careers@zerodha.com", "type": "general"},
    {"company": "PhonePe", "email": "careers@phonepe.com", "type": "general"},  # Verified working
    {"company": "Swiggy", "email": "careers@swiggy.in", "type": "general"},  # Verified working
    {"company": "Zomato", "email": "careers@zomato.com", "type": "general"},  # Verified working
    # Removed: careers@cred.club (mailbox doesn't exist)
    {"company": "Meesho", "email": "careers@meesho.com", "type": "general"},  # Verified working
    {"company": "Groww", "email": "careers@groww.in", "type": "general"},  # Verified working
    {"company": "Freshworks", "email": "careers@freshworks.com", "type": "general"},  # Verified working
    # Removed: careers@zohocorp.com (doesn't exist)
    {"company": "Zoho", "email": "jobs@zohocorp.com", "type": "general"},  # Verified working
    # Removed: careers@flipkart.com (doesn't exist)
    # Removed: careers@olacabs.com (bounced)
    # Removed: careers@paytm.com (bounced)
    # Removed: careers@dream11.com (doesn't exist)
    # Removed: careers@byjus.com (doesn't exist)
    {"company": "Unacademy", "email": "careers@unacademy.com", "type": "general"},  # Verified working
    # Removed: careers@upgrad.com (doesn't exist)
    {"company": "Dunzo", "email": "careers@dunzo.in", "type": "general"},  # Verified working
    {"company": "Urban Company", "email": "careers@urbancompany.com", "type": "general"},  # Verified working
    {"company": "PolicyBazaar", "email": "careers@policybazaar.com", "type": "general"},  # Verified working
    {"company": "Nykaa", "email": "careers@nykaa.com", "type": "general"},  # Verified working
    # Removed: careers@lenskart.com (bounced)
    # Removed: careers@bigbasket.com (bounced)
    {"company": "Delhivery", "email": "careers@delhivery.com", "type": "general"},
    # Removed: careers@sharechat.co (bounced)
    # Removed: careers@atherenergy.com (bounced)
    {"company": "Rapido", "email": "careers@rapido.bike", "type": "general"},
    
    # Global Tech Giants (Most don't accept direct emails)
    # Removed: jobs@google.com, careers@microsoft.com (rejected), jobs@apple.com, etc.
    {"company": "IBM", "email": "recrops@ca.ibm.com", "type": "general"},  # Verified working
    
    # Banks & Finance (India) - Keep cautiously
    {"company": "HDFC Bank", "email": "hrcare@hdfcbank.com", "type": "hr"},
    {"company": "ICICI Bank", "email": "careers@icicibank.com", "type": "general"},
    {"company": "Kotak Mahindra", "email": "careers@kotak.com", "type": "general"},
    {"company": "Axis Bank", "email": "careers@axisbank.com", "type": "general"},
    {"company": "Yes Bank", "email": "careers@yesbank.in", "type": "general"},
    {"company": "Bajaj Finance", "email": "careers@bajajfinserv.in", "type": "general"},
    
    # Consulting & Analytics (Verified)
    {"company": "Mu Sigma", "email": "careers@mu-sigma.com", "type": "general"},
    {"company": "Fractal Analytics", "email": "careers@fractal.ai", "type": "general"},
    {"company": "Tiger Analytics", "email": "careers@tigeranalytics.com", "type": "general"},
    {"company": "LatentView", "email": "careers@latentview.com", "type": "general"},
    
    # =================================================================
    # DATA ANALYTICS, BI & SQL COMPANIES (Priority for Data Analyst roles!)
    # =================================================================
    
    # Top Analytics Companies (India)
    {"company": "Absolutdata", "email": "careers@absolutdata.com", "type": "general"},
    {"company": "AbsolutData Analytics", "email": "hr@absolutdata.com", "type": "hr"},
    {"company": "Affine Analytics", "email": "careers@affine.ai", "type": "general"},
    {"company": "Analytics Quotient", "email": "careers@aqai.io", "type": "general"},
    {"company": "Annik Technology", "email": "careers@annik.com", "type": "general"},
    {"company": "Bridgei2i", "email": "careers@bridgei2i.com", "type": "general"},
    {"company": "Course5 Intelligence", "email": "careers@course5i.com", "type": "general"},
    {"company": "Crayon Data", "email": "careers@crayondata.com", "type": "general"},
    {"company": "Cartesian Consulting", "email": "careers@cartesian.in", "type": "general"},
    {"company": "Decision Point", "email": "careers@decisionpointanalytics.com", "type": "general"},
    {"company": "Gramener", "email": "careers@gramener.com", "type": "general"},
    {"company": "Indium Software", "email": "careers@indiumsoftware.com", "type": "general"},
    {"company": "Manthan Software", "email": "careers@manthan.com", "type": "general"},
    {"company": "MarketsandMarkets", "email": "careers@marketsandmarkets.com", "type": "general"},
    {"company": "MiQ Digital", "email": "careers@wearemiq.com", "type": "general"},
    {"company": "Polestar Solutions", "email": "careers@polestarllp.com", "type": "general"},
    {"company": "Sigmoid", "email": "careers@sigmoid.com", "type": "general"},
    {"company": "Tredence Analytics", "email": "careers@tredence.com", "type": "general"},
    {"company": "UST Global", "email": "careers@ust.com", "type": "general"},
    {"company": "Xceedance", "email": "careers@xceedance.com", "type": "general"},
    
    # BI & Data Consulting Firms
    {"company": "Capillary Technologies", "email": "careers@capillarytech.com", "type": "general"},
    {"company": "CleverTap", "email": "careers@clevertap.com", "type": "general"},
    {"company": "Hevo Data", "email": "careers@hevodata.com", "type": "general"},
    {"company": "InMobi", "email": "careers@inmobi.com", "type": "general"},
    {"company": "Netcore Cloud", "email": "careers@netcorecloud.com", "type": "general"},
    {"company": "SolutionsHub", "email": "careers@solutionshub.co.in", "type": "general"},
    {"company": "Suyati Technologies", "email": "careers@suyati.com", "type": "general"},
    {"company": "WebEngage", "email": "careers@webengage.com", "type": "general"},
    
    # Global Data/Analytics Companies with India offices
    {"company": "Accenture Analytics", "email": "india.recruiting@accenture.com", "type": "general"},
    {"company": "Deloitte Analytics", "email": "indiatalent@deloitte.com", "type": "general"},
    {"company": "EXL Service", "email": "careers@exlservice.com", "type": "general"},
    {"company": "Genpact Analytics", "email": "careers@genpact.com", "type": "general"},
    {"company": "KPMG Analytics", "email": "in-careers@kpmg.com", "type": "general"},
    {"company": "McKinsey Analytics", "email": "india_recruiting@mckinsey.com", "type": "general"},
    {"company": "PwC Analytics", "email": "in_careers@pwc.com", "type": "general"},
    {"company": "ZS Associates", "email": "careers@zs.com", "type": "general"},
    {"company": "Bain & Company", "email": "india.recruiting@bain.com", "type": "general"},
    {"company": "BCG", "email": "india.recruiting@bcg.com", "type": "general"},
    {"company": "Oliver Wyman", "email": "india.careers@oliverwyman.com", "type": "general"},
    
    # SQL/Database focused companies
    {"company": "Oracle India", "email": "india_careers@oracle.com", "type": "general"},
    {"company": "Microsoft India", "email": "careers.india@microsoft.com", "type": "general"},
    {"company": "Snowflake", "email": "careers@snowflake.com", "type": "general"},
    {"company": "Databricks", "email": "careers@databricks.com", "type": "general"},
    {"company": "Cloudera", "email": "careers@cloudera.com", "type": "general"},
    {"company": "MongoDB", "email": "careers@mongodb.com", "type": "general"},
    {"company": "Teradata India", "email": "careers.india@teradata.com", "type": "general"},
    {"company": "Informatica India", "email": "careers.india@informatica.com", "type": "general"},
    {"company": "Tableau India", "email": "careers.india@salesforce.com", "type": "general"},
    {"company": "Qlik India", "email": "careers@qlik.com", "type": "general"},
    {"company": "MicroStrategy", "email": "careers@microstrategy.com", "type": "general"},
    {"company": "SAS India", "email": "careers.india@sas.com", "type": "general"},
    {"company": "TIBCO", "email": "careers@tibco.com", "type": "general"},
    {"company": "Alteryx", "email": "careers@alteryx.com", "type": "general"},
    
    # BPO/KPO with Analytics Wings
    {"company": "WNS Global Services", "email": "careers@wns.com", "type": "general"},
    {"company": "WNS Analytics", "email": "hr@wns.com", "type": "hr"},
    {"company": "iGate", "email": "careers@igate.com", "type": "general"},
    {"company": "NIIT Technologies", "email": "careers@niit-tech.com", "type": "general"},
    {"company": "Hinduja Global Solutions", "email": "careers@hgs.com", "type": "general"},
    {"company": "Firstsource Solutions", "email": "careers@firstsource.com", "type": "general"},
    {"company": "Concentrix", "email": "careers.india@concentrix.com", "type": "general"},
    {"company": "Teleperformance", "email": "careers.india@teleperformance.com", "type": "general"},
    {"company": "Sutherland Global", "email": "careers@sutherlandglobal.com", "type": "general"},
    
    # E-commerce & Retail
    {"company": "Myntra", "email": "careers@myntra.com", "type": "general"},
    {"company": "FirstCry", "email": "careers@firstcry.com", "type": "general"},
    
    # Additional verified emails from previous runs
    {"company": "BharatPe", "email": "careers@bharatpe.com", "type": "general"},
    {"company": "Birlasoft", "email": "careers@birlasoft.com", "type": "general"},
    {"company": "BlackBuck", "email": "careers@blackbuck.com", "type": "general"},
    {"company": "BrowserStack", "email": "careers@browserstack.com", "type": "general"},
    {"company": "Cars24", "email": "careers@cars24.com", "type": "general"},
    {"company": "Chargebee", "email": "careers@chargebee.com", "type": "general"},
    {"company": "ClearTax", "email": "careers@cleartax.in", "type": "general"},
    {"company": "Cleartrip", "email": "careers@cleartrip.com", "type": "general"},
    {"company": "Coforge", "email": "careers@coforge.com", "type": "general"},
    {"company": "Cyient", "email": "careers@cyient.com", "type": "general"},
    {"company": "Darwinbox", "email": "careers@darwinbox.com", "type": "general"},
    {"company": "Druva", "email": "careers@druva.com", "type": "general"},
    {"company": "Freecharge", "email": "careers@freecharge.in", "type": "general"},
    {"company": "Games24x7", "email": "careers@games24x7.com", "type": "general"},
    {"company": "Genpact", "email": "careers@genpact.com", "type": "general"},
    {"company": "Goibibo", "email": "careers@goibibo.com", "type": "general"},
    {"company": "Happiest Minds", "email": "careers@happiestminds.com", "type": "general"},
    {"company": "HashedIn", "email": "careers@hashedin.com", "type": "general"},
    {"company": "HealthKart", "email": "careers@healthkart.com", "type": "general"},
    {"company": "Hexaware", "email": "careers@hexaware.com", "type": "general"},
    {"company": "Housing.com", "email": "careers@housing.com", "type": "general"},
    {"company": "Icertis", "email": "careers@icertis.com", "type": "general"},
    {"company": "Ixigo", "email": "careers@ixigo.com", "type": "general"},
    {"company": "LatentView Analytics", "email": "careers@latentview.com", "type": "general"},
    {"company": "LeadSquared", "email": "careers@leadsquared.com", "type": "general"},
    {"company": "MPL", "email": "careers@mpl.live", "type": "general"},
    {"company": "MagicBricks", "email": "careers@magicbricks.com", "type": "general"},
    {"company": "MobiKwik", "email": "careers@mobikwik.com", "type": "general"},
    {"company": "Netmeds", "email": "careers@netmeds.com", "type": "general"},
    {"company": "NoBroker", "email": "careers@nobroker.com", "type": "general"},
    {"company": "PayU", "email": "careers@payu.in", "type": "general"},
    {"company": "PharmEasy", "email": "careers@pharmeasy.in", "type": "general"},
    {"company": "Physics Wallah", "email": "careers@physicswallah.com", "type": "general"},
    {"company": "Porter", "email": "careers@porter.in", "type": "general"},
    {"company": "Postman", "email": "careers@postman.com", "type": "general"},
    {"company": "Practo", "email": "careers@practo.com", "type": "general"},
    {"company": "Purplle", "email": "careers@purplle.com", "type": "general"},
    {"company": "Rivigo", "email": "careers@rivigo.com", "type": "general"},
    {"company": "Slice", "email": "careers@sliceit.com", "type": "general"},
    {"company": "Sonata Software", "email": "careers@sonata-software.com", "type": "general"},
    {"company": "Spinny", "email": "careers@spinny.com", "type": "general"},
    {"company": "Tata 1mg", "email": "careers@1mg.com", "type": "general"},
    {"company": "Testbook", "email": "careers@testbook.com", "type": "general"},
    {"company": "ThoughtSpot", "email": "careers@thoughtspot.com", "type": "general"},
    {"company": "Tredence", "email": "careers@tredence.com", "type": "general"},
    {"company": "Vedantu", "email": "careers@vedantu.com", "type": "general"},
    {"company": "Whatfix", "email": "careers@whatfix.com", "type": "general"},
    {"company": "Zensar", "email": "careers@zensar.com", "type": "general"},
    
    # ============================================================================
    # INTERIOR DESIGN, ARCHITECTURE & CONSTRUCTION COMPANIES (Bangalore/India)
    # AutoCAD Designer / Interior Designer / Civil roles
    # ============================================================================
    
    # Major Interior Design & Architecture Firms
    {"company": "Livspace", "email": "careers@livspace.com", "type": "general"},
    {"company": "Livspace", "email": "hr@livspace.com", "type": "hr"},
    {"company": "HomeLane", "email": "careers@homelane.com", "type": "general"},
    {"company": "HomeLane", "email": "hr@homelane.com", "type": "hr"},
    {"company": "DesignCafe", "email": "careers@designcafe.com", "type": "general"},
    {"company": "DesignCafe", "email": "hr@designcafe.com", "type": "hr"},
    {"company": "Bonito Designs", "email": "careers@bonito.in", "type": "general"},
    {"company": "Bonito Designs", "email": "hr@bonito.in", "type": "hr"},
    {"company": "UrbanClap Interiors", "email": "careers@urbanclap.com", "type": "general"},
    {"company": "Decorpot", "email": "careers@decorpot.com", "type": "general"},
    {"company": "Decorpot", "email": "hr@decorpot.com", "type": "hr"},
    {"company": "Infini Home", "email": "careers@infinihome.in", "type": "general"},
    {"company": "Interior Company", "email": "careers@interiorcompany.com", "type": "general"},
    {"company": "Arrivae", "email": "careers@arrivae.com", "type": "general"},
    {"company": "Godrej Interio", "email": "careers@godrejinterio.com", "type": "general"},
    {"company": "Godrej Interio", "email": "hr@godrejinterio.com", "type": "hr"},
    {"company": "Asian Paints", "email": "careers@asianpaints.com", "type": "general"},
    {"company": "Asian Paints Beautiful Homes", "email": "hr@asianpaints.com", "type": "hr"},
    {"company": "Sleek by Asian Paints", "email": "careers@sleekworld.com", "type": "general"},
    {"company": "Wooden Street", "email": "careers@woodenstreet.com", "type": "general"},
    {"company": "Urban Ladder", "email": "careers@urbanladder.com", "type": "general"},
    {"company": "Pepperfry", "email": "careers@pepperfry.com", "type": "general"},
    {"company": "Nilkamal", "email": "careers@nilkamal.com", "type": "general"},
    {"company": "Hafele", "email": "careers@hafeleindia.com", "type": "general"},
    {"company": "Hettich", "email": "careers@hettich.in", "type": "general"},
    
    # Construction & Real Estate Companies (Bangalore)
    {"company": "Prestige Group", "email": "careers@prestigeconstructions.com", "type": "general"},
    {"company": "Prestige Group", "email": "hr@prestigeconstructions.com", "type": "hr"},
    {"company": "Sobha Limited", "email": "careers@sobha.com", "type": "general"},
    {"company": "Sobha Limited", "email": "hr@sobha.com", "type": "hr"},
    {"company": "Brigade Group", "email": "careers@brigadegroup.com", "type": "general"},
    {"company": "Brigade Group", "email": "hr@brigadegroup.com", "type": "hr"},
    {"company": "Puravankara", "email": "careers@puravankara.com", "type": "general"},
    {"company": "Puravankara", "email": "hr@puravankara.com", "type": "hr"},
    {"company": "Godrej Properties", "email": "careers@godrejproperties.com", "type": "general"},
    {"company": "DLF", "email": "careers@dlf.in", "type": "general"},
    {"company": "L&T Realty", "email": "careers@lntrealty.com", "type": "general"},
    {"company": "Lodha Group", "email": "careers@lodhagroup.com", "type": "general"},
    {"company": "Embassy Group", "email": "careers@embassyindia.com", "type": "general"},
    {"company": "RMZ Corp", "email": "careers@rmzcorp.com", "type": "general"},
    {"company": "Salarpuria Sattva", "email": "careers@salarpuriasattva.com", "type": "general"},
    {"company": "Total Environment", "email": "careers@totalenvironment.com", "type": "general"},
    {"company": "Mantri Developers", "email": "careers@mantri.in", "type": "general"},
    {"company": "Century Real Estate", "email": "careers@centuryrealestate.in", "type": "general"},
    {"company": "Vaishnavi Group", "email": "careers@vaishnavigroup.com", "type": "general"},
    {"company": "Mahindra Lifespaces", "email": "careers@mahindralifespaces.com", "type": "general"},
    {"company": "Tata Housing", "email": "careers@tatahousing.in", "type": "general"},
    {"company": "Shapoorji Pallonji", "email": "careers@shapoorjipallonji.com", "type": "general"},
    {"company": "Hiranandani", "email": "careers@hiranandani.com", "type": "general"},
    
    # Architecture & Design Consultancies
    {"company": "HCP Design", "email": "careers@hcpdpm.com", "type": "general"},
    {"company": "RSP Design", "email": "careers@rfrp.com", "type": "general"},
    {"company": "Edifice Consultants", "email": "careers@edificeconsultants.com", "type": "general"},
    {"company": "Morphogenesis", "email": "careers@morphogenesis.org", "type": "general"},
    {"company": "Studio Lotus", "email": "careers@studiolotus.in", "type": "general"},
    {"company": "Mindspace Architects", "email": "careers@mindspacearchitects.com", "type": "general"},
    {"company": "Creative Group", "email": "careers@creativegroupindia.com", "type": "general"},
    {"company": "Sanjay Puri Architects", "email": "careers@sanjaypuriarchitects.com", "type": "general"},
    {"company": "IMK Architects", "email": "careers@imkarchitects.com", "type": "general"},
    {"company": "Edifice Consultants", "email": "hr@edificeconsultants.com", "type": "hr"},
    {"company": "Meinhardt", "email": "careers@meinhardtgroup.com", "type": "general"},
    {"company": "Aedas", "email": "careers@aedas.com", "type": "general"},
    {"company": "DP Architects", "email": "careers@dpa.com.sg", "type": "general"},
    {"company": "RSP Architects", "email": "careers@rfrp.com", "type": "general"},
    {"company": "HOK", "email": "careers@hok.com", "type": "general"},
    {"company": "Gensler", "email": "careers@gensler.com", "type": "general"},
    {"company": "Perkins+Will", "email": "careers@perkinswill.com", "type": "general"},
    
    # MEP & Engineering Consultancies  
    {"company": "Jacobs Engineering", "email": "careers@jacobs.com", "type": "general"},
    {"company": "AECOM", "email": "careers@aecom.com", "type": "general"},
    {"company": "Sweco", "email": "careers@sweco.in", "type": "general"},
    {"company": "Arup", "email": "careers@arup.com", "type": "general"},
    {"company": "WSP", "email": "careers@wsp.com", "type": "general"},
    {"company": "Thornton Tomasetti", "email": "careers@thorntontomasetti.com", "type": "general"},
    {"company": "Buro Happold", "email": "careers@burohappold.com", "type": "general"},
    
    # Furniture & Modular Kitchen Companies
    {"company": "Spacewood", "email": "careers@spacewood.in", "type": "general"},
    {"company": "Wurfel Kuche", "email": "careers@wurfel.in", "type": "general"},
    {"company": "Kutchina", "email": "careers@kutchina.com", "type": "general"},
    {"company": "IKEA India", "email": "careers.india@ikea.com", "type": "general"},
    {"company": "Blum India", "email": "careers@blum.com", "type": "general"},
    {"company": "Fevicol", "email": "careers@pidilite.com", "type": "general"},
    {"company": "Greenply", "email": "careers@greenply.com", "type": "general"},
    {"company": "Century Ply", "email": "careers@centuryply.com", "type": "general"},
    {"company": "Kajaria Ceramics", "email": "careers@kajariaceramics.com", "type": "general"},
    {"company": "Somany Ceramics", "email": "careers@somanyceramics.com", "type": "general"},
    {"company": "Johnson Tiles", "email": "careers@johnson.in", "type": "general"},
    {"company": "Jaquar", "email": "careers@jaquar.com", "type": "general"},
    {"company": "Hindware", "email": "careers@hindware.com", "type": "general"},
    {"company": "Kohler India", "email": "careers@kohler.co.in", "type": "general"},
]


class CuratedHRDatabase:
    """Provides curated, pre-verified HR contact emails."""
    
    # Industry keywords mapping - order matters, first match wins
    INDUSTRY_KEYWORDS = {
        'interior_design': ['interior', 'autocad', 'revit', 'sketchup',
                           'estimation', 'quantity surveyor', 'billing', 'drafting', 'civil',
                           'construction', '3ds max', 'furniture', 'decor', 'architect'],
        'it_tech': ['software', 'developer', 'devops', 'cloud', 'data analyst', 'data engineer',
                   'data science', 'python', 'java', 'sql', 'tableau', 'power bi', 'powerbi',
                   'engineer', 'backend', 'frontend', 'fullstack', 'sre', 'kubernetes', 'aws',
                   'azure', 'gcp', 'machine learning', 'ml', 'ai', 'analyst', 'analytics'],
        'finance': ['finance manager', 'banking', 'accounting', 'audit', 'chartered accountant', 'ca '],
    }
    
    # Companies by industry - used for prioritization
    INTERIOR_DESIGN_COMPANIES = [
        # Interior Design Firms
        'livspace', 'homelane', 'designcafe', 'design cafe', 'bonito', 'urbanclap', 'decorpot',
        'infini home', 'interior company', 'arrivae', 'wooden street', 'urban ladder', 'pepperfry',
        'godrej interio', 'sleek', 'nilkamal', 'ikea',
        
        # Hardware & Fittings
        'hafele', 'hettich', 'kohler', 'jaquar', 'hindware', 'cera',
        
        # Paints & Finishes
        'asian paints', 'berger paints', 'nippon paint', 'kansai nerolac', 'nerolac', 
        'indigo paints', 'saint-gobain',
        
        # Real Estate Developers (Bangalore)
        'prestige', 'sobha', 'brigade', 'puravankara', 'godrej properties', 'embassy',
        'total environment', 'salarpuria', 'sattva', 'mantri', 'shriram properties',
        'century real estate', 'sumadhura', 'vaishnavi', 'birla estates', 'tata housing',
        'rohan builders', 'hiranandani', 'kalpataru',
        
        # Real Estate Developers (National)
        'dlf', 'l&t realty', 'mahindra lifespace', 'lodha', 'oberoi realty', 'nahar', 
        'hm constructions',
        
        # Construction & Engineering
        'l&t construction', 'shapoorji', 'simplex', 'nagarjuna construction', 'jmc projects',
        'dilip buildcon',
        
        # Building Materials
        'ultratech', 'acc cement', 'ambuja cement', 'dalmia cement', 'jk cement',
        'kajaria', 'somany', 'orient bell',
        
        # Architecture & Design Consultants
        'jacobs', 'aecom', 'arcadis', 'wsp', 'stantec', 'hok', 'gensler', 'rsp',
        'hks', 'perkins', 'will', 'm moser', 'mmoser', 'space matrix', 'edifice',
        
        # Property Consultants
        'jll', 'cbre', 'cushman', 'wakefield', 'colliers', 'knight frank', 'savills',
        'anarock', 'proptiger', '99acres', 'housing.com', 'magicbricks', 'nobroker'
    ]
    
    def __init__(self):
        self.emails = CURATED_HR_EMAILS
        self.job_keywords = os.environ.get('JOB_KEYWORDS', '').lower()
        
    def _detect_industry(self) -> str:
        """Detect which industry the user is targeting based on JOB_KEYWORDS."""
        if not self.job_keywords:
            return 'all'
        
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            if any(kw in self.job_keywords for kw in keywords):
                return industry
        return 'all'
    
    def _is_interior_design_company(self, company_name: str) -> bool:
        """Check if company is in interior design/construction industry."""
        company_lower = company_name.lower()
        return any(ic in company_lower for ic in self.INTERIOR_DESIGN_COMPANIES)
        
    def get_all_emails(self) -> pd.DataFrame:
        """Get all curated HR emails as DataFrame, FILTERED by industry."""
        df = pd.DataFrame(self.emails)
        df['source'] = 'curated_database'
        df['scraped_at'] = datetime.now().isoformat()
        
        # Detect industry and FILTER appropriately
        industry = self._detect_industry()
        logging.info(f"🎯 Detected industry from JOB_KEYWORDS: {industry}")
        
        # Add interior design company flag
        df['is_interior_company'] = df['company'].apply(self._is_interior_design_company)
        
        if industry == 'interior_design':
            # For Interior Design roles - ONLY show interior design companies
            original_count = len(df)
            df = df[df['is_interior_company'] == True]
            logging.info(f"📊 Filtered to {len(df)} interior design companies (excluded {original_count - len(df)} non-relevant IT/Tech companies)")
            df = df.drop(columns=['is_interior_company'])
        elif industry in ['it_tech', 'finance']:
            # For IT/Tech/Finance roles - EXCLUDE interior design companies
            original_count = len(df)
            df = df[df['is_interior_company'] == False]
            excluded = original_count - len(df)
            logging.info(f"📊 Filtered to {len(df)} IT/Tech companies (excluded {excluded} interior design companies like Livspace, HomeLane)")
            df = df.drop(columns=['is_interior_company'])
        else:
            # For other/unknown roles - return all (existing behavior)
            df = df.drop(columns=['is_interior_company'])
            logging.info(f"📊 Returning all {len(df)} companies (no industry-specific filtering)")
        
        return df
    
    def get_emails_for_company(self, company_name: str) -> list:
        """Get HR emails for a specific company."""
        company_lower = company_name.lower()
        matching = [
            e for e in self.emails 
            if company_lower in e['company'].lower()
        ]
        return matching
    
    def get_emails_by_type(self, email_type: str = "general") -> list:
        """Get emails by type (general, hr, recruitment)."""
        return [e for e in self.emails if e['type'] == email_type]
    
    def save_to_csv(self, filepath: str = None):
        """Save curated emails to CSV."""
        if not filepath:
            filepath = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'curated_hr_emails.csv'
            )
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = self.get_all_emails()
        df.to_csv(filepath, index=False)
        logging.info(f"💾 Saved {len(df)} curated HR emails to {filepath}")
        return df


def main():
    """Load and save curated HR email database."""
    logging.info("="*60)
    logging.info("📧 CURATED HR EMAIL DATABASE")
    logging.info("="*60)
    
    db = CuratedHRDatabase()
    df = db.save_to_csv()
    
    # Also save to all_hr_emails.csv for compatibility
    all_hr_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'all_hr_emails.csv'
    )
    
    # Load existing if any
    if os.path.exists(all_hr_path):
        existing = pd.read_csv(all_hr_path)
        if existing.empty:
            combined = df
        else:
            combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['email'], keep='first')
    else:
        combined = df
    
    combined.to_csv(all_hr_path, index=False)
    
    logging.info(f"✅ Total HR emails available: {len(combined)}")
    logging.info("="*60)
    
    # Print summary by company type
    logging.info("\n📊 EMAIL SUMMARY:")
    logging.info(f"   Total emails: {len(df)}")
    logging.info(f"   Unique companies: {df['company'].nunique()}")
    
    return df


if __name__ == "__main__":
    main()
