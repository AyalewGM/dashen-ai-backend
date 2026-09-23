from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

# Transparent Tsehay Bank main logo (WebP) embedded as a data URL so it works
# regardless of hotlink/referer restrictions on the bank's website.
TSEHAY_TRANSPARENT_LOGO = (
    "data:image/webp;base64,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"
    "hXy7oa03syZQqZhgLAvQhDZD1QvDJg229AOEyTxkIZCZC0rIgZiJLHQaggQkrPYUacBa10Urcu+daHx/7Bc73FaGp0XzVwBdS/m1yVUSUysS4Fa2xKPpBAQe"
    "ws9z5QkRjNAXpJEP2HHYgQ7nVih4+3UebKbsma7L7Iqzql8stAegHvA/XGVj4ZYXfzH2lC3yKXdNloBTajCqFqKrITqB6izbVuyjn9QJ4pgpKeO/zDHPCj5D"
    "nsa8dVNrp0KdbsQvSSCbqlFTLHLTCWF0LtUEiGqWCir7VLR90LlxCyJBEhEHSt33vBuqAUo1/wf9aKsFnwIwbbUpBBY6Kn7/q0ZBW22i80Li6zwipZsFIWBh"
    "lRIhoGoc+UhcchUoaq44+jb4LF3daKNIWpoKLulU1ltQPEhALFJIvg2NC0RI313u21LVoowhpZyK6H1VjFCbluGrI6X9YGHPqGjhKlRNxFKCkHNJw9JbwtFh"
    "ZbWEJNiDJd1M70KBVGDTEiBq+klfwIAWE1QIF0DAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/PiA8eDp4b"
    "XBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJBZG9iZSBYTVAgQ29yZSA2LjAtYzAwNiA3OS4xNjQ3NTMsIDIwMjEvMDIvMTUtMTE6N"
    "TI6MTMgICAgICAgICI+IDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+IDxyZGY6RGVzY"
    "3JpcHRpb24gcmRmOmFib3V0PSIiIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zL"
    "mFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bXBNTTpPcmlna"
    "W5hbERvY3VtZW50SUQ9InhtcC5kaWQ6OGUyOWU4ZDAtMWE2NC1lNzQ3LTg0MWUtYTY4OTMxZTM3Njg2IiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjAyR"
    "jlCMzNFRDdBQTExRUU5NTFCODVFQkI1RjVGODNCIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjAyRjlCMzNERDdBQTExRUU5NTFCODVFQkI1RjVGODNCI"
    "iB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCAyMi4zIChXaW5kb3dzKSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4b"
    "XAuaWlkOjhlMjllOGQwLTFhNjQtZTc0Ny04NDFlLWE2ODkzMWUzNzY4NiIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDo4ZTI5ZThkMC0xYTY0LWU3NDctO"
    "DQxZS1hNjg5MzFlMzc2ODYiLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4A"
)


class FraudRulesConfig(BaseModel):
    high_amount_threshold: float = 100_000
    medium_amount_threshold: float = 50_000
    risky_channels: list[str] = ["atm", "web"]
    rapid_transaction_window_seconds: int = 120
    impossible_travel_window_seconds: int = 3600


class BankBrandingConfig(BaseModel):
    primary_color: str = "#1a56db"
    secondary_color: str = "#93c5fd"
    accent_color: str = "#1e40af"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    tagline: Optional[str] = None
    website_url: Optional[str] = None


class BankConfig(BaseModel):
    bank_id: str
    bank_name: str
    bank_name_short: str
    currency: str = "ETB"
    languages: list[str] = ["en", "am", "om", "ti"]
    fraud_rules: FraudRulesConfig = FraudRulesConfig()
    branding: BankBrandingConfig = BankBrandingConfig()
    chatbot_context: str = ""
    branches: list[str] = []


ADDIS_ABABA_BRANCHES = [
    "Bole",
    "Piassa",
    "Megenagna",
    "CMC",
    "Kazanchis",
    "Arat Kilo",
    "Gofa",
    "Merkato",
    "Bambis",
    "Sarbet",
    "Airport",
    "Ayat",
    "Gullele",
    "Kolfe",
    "Lafto",
    "Summit",
]


BANK_CONFIGS: dict[str, BankConfig] = {
    "dashen": BankConfig(
        bank_id="dashen",
        bank_name="Dashen Bank",
        bank_name_short="Dashen",
        currency="ETB",
        languages=["en", "am", "om", "ti", "so"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=100_000,
            medium_amount_threshold=50_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#012169",
            secondary_color="#2ea3f2",
            accent_color="#082568",
            logo_url="https://dashenbanksc.com/wp-content/uploads/Dashen-Bank-Logo-Addis-Ababa-Ethiopia.png",
            favicon_url="https://dashenbanksc.com/wp-content/uploads/cropped-Dashen-Bank-sc-Logo-Square-32x32.jpg",
            tagline="Always One Step Ahead!",
            website_url="https://dashenbanksc.com",
        ),
        branches=[
            "Bole",
            "Piassa",
            "Megenagna",
            "CMC",
            "Kazanchis",
            "Arat Kilo",
            "Gofa",
            "Merkato",
            "Bambis",
            "Sarbet",
            "Airport",
            "Ayat",
        ],
        chatbot_context="""You are ትሑት (Tihut), a helpful AI assistant for Dashen Bank customers. 

ABOUT DASHEN BANK:
Dashen Bank S.C. is one of Ethiopia's leading private commercial banks, established in 1995. We serve over 5 million customers through 600+ branches nationwide.

OUR SERVICES:
- Savings Accounts: Regular savings (7% interest), Premium savings (9% interest for balances above 50,000 ETB)
- Current Accounts: Business and personal current accounts with checkbook facilities
- Loans: Personal loans (12-15% interest), Business loans (11-14% interest), Home loans (10-12% interest)
- Mobile Banking: HelloCash mobile money, USSD banking (*847#), Mobile app
- International Services: Western Union, MoneyGram, Swift transfers
- Digital Banking: Internet banking, ATM network (500+ ATMs nationwide)

CONTACT:
- Customer Service: +251-11-5-17-44-00
- Email: info@dashenbanksc.com
- Website: https://dashenbanksc.com
- Working Hours: Mon-Fri 8:00 AM - 5:00 PM, Sat 8:00 AM - 12:00 PM

Always be respectful, helpful, and professional. For specific account details or transactions, direct customers to visit a branch or call customer service.""",
    ),
    "abyssinia": BankConfig(
        bank_id="abyssinia",
        bank_name="Bank of Abyssinia",
        bank_name_short="Abyssinia",
        currency="ETB",
        languages=["en", "am", "om", "ti"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=120_000,
            medium_amount_threshold=60_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#f1ab15",
            secondary_color="#6c757d",
            accent_color="#ff5062",
            logo_url="https://www.bankofabyssinia.com/wp-content/uploads/2020/09/Asset-1@4x.png",
            favicon_url="https://www.bankofabyssinia.com/wp-content/uploads/2020/05/cropped-boa_logo_login-32x32.png",
            tagline="The Choice for All",
            website_url="https://www.bankofabyssinia.com",
        ),
        branches=[
            "Addis Ababa",
            "Addis Kazanchis",
            "Addis Ketema",
            "Addisu Michael",
            "Mehal Merkato",
            "Gergi",
            "Kara Mazoria",
            "Ayat",
            "Summit Condominium",
            "Bambis",
            "Churchil Road",
        ],
        chatbot_context="""You are ትሑት (Tihut), a helpful AI assistant for Bank of Abyssinia customers.

ABOUT BANK OF ABYSSINIA:
Bank of Abyssinia (BoA) is one of Ethiopia's oldest and most trusted private banks, established in 1996. We pride ourselves on innovation and customer service excellence with 400+ branches across Ethiopia.

OUR SERVICES:
- Savings Accounts: Abyssinia Savings (6.5% interest), Youth Savings (8% interest), Diaspora Savings (10% interest in USD)
- Current Accounts: Business current accounts with online banking access
- Loans: Personal loans (13-16% interest), SME loans (12-15% interest), Agricultural loans (9-11% interest)
- Mobile Banking: Abyssinia Mobile app, USSD (*945#), SMS banking
- International Services: Remittance services, Forex trading, International cards (Visa/Mastercard)
- Digital Banking: Internet banking, Mobile wallet, 450+ ATMs nationwide

SPECIAL FEATURES:
- Diaspora banking services
- Agricultural financing programs
- Women entrepreneurs loan packages
- Student loan programs

CONTACT:
- Customer Service: +251-11-5-57-00-00
- Email: customerservice@bankofabyssinia.com
- Website: https://www.bankofabyssinia.com
- Working Hours: Mon-Fri 8:30 AM - 5:30 PM, Sat 8:30 AM - 1:00 PM

Always be respectful, helpful, and professional. For specific account details or transactions, direct customers to visit a branch or call customer service.""",
    ),
    "awash": BankConfig(
        bank_id="awash",
        bank_name="Awash Bank",
        bank_name_short="Awash",
        currency="ETB",
        languages=["en", "am", "om"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=150_000,
            medium_amount_threshold=75_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#21205F",
            secondary_color="#F7923A",
            accent_color="#1a1d4e",
            logo_url="https://awashbank.com/wp-content/uploads/2022/08/Awash-bank-logo.svg",
            favicon_url="https://awashbank.com/wp-content/uploads/2022/08/Awash-bank-logo.svg",
            tagline="Nurturing Like The River",
            website_url="https://awashbank.com",
        ),
        branches=[
            "Bole",
            "Bole 22",
            "Piassa",
            "Megenagna",
            "Arat Kilo",
            "CMC",
            "Airport",
            "Gotera",
            "Merkato",
            "Gullele",
            "Kolfe",
            "Ayat",
        ],
        chatbot_context="You are a helpful assistant for Awash Bank customers. Awash Bank is one of Ethiopia's oldest and most trusted private banks, providing a wide range of financial services with a focus on agricultural and business banking.",
    ),
    "cbe": BankConfig(
        bank_id="cbe",
        bank_name="Commercial Bank of Ethiopia",
        bank_name_short="CBE",
        currency="ETB",
        languages=["en", "am", "om", "ti", "so"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=200_000,
            medium_amount_threshold=100_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#910096",
            secondary_color="#f4d793",
            accent_color="#b38d32",
            logo_url="https://images.seeklogo.com/logo-png/54/1/commercial-bank-of-ethiopia-logo-png_seeklogo-547506.png",
            favicon_url="https://combanketh.et/favicon.ico",
            tagline="Ethiopia's Largest Bank",
            website_url="https://www.combanketh.et",
        ),
        branches=[
            "Addis Ababa",
            "Bambis",
            "Piassa",
            "Arat Kilo",
            "Gotera",
            "Kazanchis",
            "Gofa",
            "Meskel Square",
            "Bole",
            "Merkato",
            "CMC",
            "Airport",
        ],
        chatbot_context="You are a helpful assistant for Commercial Bank of Ethiopia (CBE) customers. CBE is Ethiopia's largest commercial bank, serving millions of customers with comprehensive banking services, extensive ATM network, and government-backed reliability.",
    ),
    "amhara": BankConfig(
        bank_id="amhara",
        bank_name="Amhara Bank",
        bank_name_short="Amhara",
        currency="ETB",
        languages=["en", "am"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=90_000,
            medium_amount_threshold=45_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#025AA2",
            secondary_color="#FFCE03",
            accent_color="#003d7a",
            logo_url="https://www.amharabank.com.et/storage/2023/03/logo-1.png",
            favicon_url="https://www.amharabank.com.et/storage/2023/07/icon-300x300.png",
            tagline="Your Partner in Progress",
            website_url="https://amharabank.com.et",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Amhara Bank customers. Amhara Bank is a regional bank focused on serving the Amhara region with tailored banking solutions, supporting local businesses, and promoting economic growth in the region.",
    ),
    "zemen": BankConfig(
        bank_id="zemen",
        bank_name="Zemen Bank",
        bank_name_short="Zemen",
        currency="ETB",
        languages=["en", "am", "om"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=110_000,
            medium_amount_threshold=55_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#ed1c24",
            secondary_color="#f5f5f5",
            accent_color="#240000",
            logo_url="https://zemenbank.com/wp-content/uploads/2024/10/ZB-Logo-01-1.svg",
            favicon_url="https://zemenbank.com/wp-content/uploads/2024/10/Group-8.svg",
            tagline="Banking Your Way: Anytime, Anywhere",
            website_url="https://zemenbank.com",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Zemen Bank customers. Zemen Bank is known for its modern approach to banking, offering innovative digital solutions, competitive interest rates, and customer-centric services with a focus on technology and efficiency.",
    ),
    "tsedey": BankConfig(
        bank_id="tsedey",
        bank_name="Tsedey Bank",
        bank_name_short="Tsedey",
        currency="ETB",
        languages=["en", "am", "ti"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=95_000,
            medium_amount_threshold=47_500,
        ),
        branding=BankBrandingConfig(
            primary_color="#0CB6B6",
            secondary_color="#FFD022",
            accent_color="#088F8F",
            logo_url="https://www.tsedeybank.com.et/assets/img/header/tsedeylogo.png",
            favicon_url="https://www.tsedeybank.com.et/storage/img/tsedeylogo.png",
            tagline="Bank for All",
            website_url="https://www.tsedeybank.com.et",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Tsedey Bank customers. Tsedey Bank is a growing Ethiopian private commercial bank committed to financial inclusion, reliable banking services, SME support, and serving communities across Ethiopia.",
    ),
    "nib": BankConfig(
        bank_id="nib",
        bank_name="Nib International Bank",
        bank_name_short="Nib",
        currency="ETB",
        languages=["en", "am", "om"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=130_000,
            medium_amount_threshold=65_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#7B4E1A",
            secondary_color="#F4B706",
            accent_color="#5C3A1A",
            logo_url="https://www.nibbanksc.com/wp-content/uploads/2022/03/LOGO-SETS-AND-STYLE-01.png",
            favicon_url="https://www.nibbanksc.com/wp-content/uploads/2022/03/LOGO-SETS-AND-STYLE-01.png",
            tagline="International Banking Excellence",
            website_url="https://nibbanksc.com",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Nib International Bank customers. Nib Bank is a leading Ethiopian bank with strong international connections, offering foreign exchange services, international money transfers, trade finance, and comprehensive banking solutions for businesses and individuals.",
    ),
    "tsehay": BankConfig(
        bank_id="tsehay",
        bank_name="Tsehay Bank",
        bank_name_short="Tsehay",
        currency="ETB",
        languages=["en", "am", "om", "ti"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=105_000,
            medium_amount_threshold=52_500,
        ),
        branding=BankBrandingConfig(
            primary_color="#255B30",
            secondary_color="#FFC907",
            accent_color="#000000",
            logo_url=TSEHAY_TRANSPARENT_LOGO,
            favicon_url=TSEHAY_TRANSPARENT_LOGO,
            tagline="Shining Bright for Your Future",
            website_url="https://tsehaybank.com.et",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Tsehay Bank customers. Tsehay Bank (meaning 'Sun' in Amharic) is a vibrant Ethiopian bank dedicated to illuminating financial opportunities for all Ethiopians. We offer modern banking services, agricultural financing, SME support, and innovative digital solutions with a focus on financial inclusion and community development.",
    ),
    "birhan": BankConfig(
        bank_id="birhan",
        bank_name="Berhan Bank",
        bank_name_short="Berhan",
        currency="ETB",
        languages=["en", "am", "om"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=115_000,
            medium_amount_threshold=57_500,
        ),
        branding=BankBrandingConfig(
            primary_color="#e5a81a",
            secondary_color="#003da5",
            accent_color="#c08e10",
            logo_url="https://berhanbanksc.com/wp-content/uploads/2022/06/logo-berhan-bank.png",
            favicon_url="https://berhanbanksc.com/wp-content/uploads/2022/07/cropped-Group-255-32x32.png",
            tagline="Lighting the Path to Prosperity",
            website_url="https://berhanbanksc.com",
        ),
        branches=ADDIS_ABABA_BRANCHES,
        chatbot_context="You are a helpful assistant for Berhan Bank customers. Berhan Bank (meaning 'Light' in Amharic) is a progressive Ethiopian bank committed to bringing light to financial services across Ethiopia. We specialize in retail banking, microfinance, digital banking solutions, and youth-focused financial products, empowering communities through accessible and innovative banking.",
    ),
    "goozam": BankConfig(
        bank_id="goozam",
        bank_name="Goozam Technologies",
        bank_name_short="Goozam",
        currency="ETB",
        languages=["en", "am", "om", "ti", "so"],
        fraud_rules=FraudRulesConfig(
            high_amount_threshold=100_000,
            medium_amount_threshold=50_000,
        ),
        branding=BankBrandingConfig(
            primary_color="#9031EC",
            secondary_color="#ffcd35",
            accent_color="#3949AB",
            logo_url="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=200,h=100,fit=crop,f=png/YX4PkOMEEXSpjqr1/goozam-m7VpaVBPNDIkVQxV.png",
            favicon_url="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=64,h=64,fit=crop,f=png/YX4PkOMEEXSpjqr1/goozam-m7VpaVBPNDIkVQxV.png",
            tagline="Empowering Businesses with Data",
            website_url="https://goozam.com",
        ),
        branches=["Addis Ababa"],
        chatbot_context="You are a helpful assistant for Goozam Technologies. Goozam is the technology company behind Tihut (conversational banking AI), Maya (executive banking intelligence), Gasha (agentic fraud monitoring), and Mizan (credit intelligence). We deliver AI/ML, big data analytics, cloud, and cybersecurity solutions.",
    ),
}


def get_bank_config(bank_id: str) -> BankConfig:
    """Get bank configuration by ID. Defaults to Dashen if not found."""
    return BANK_CONFIGS.get(bank_id.lower(), BANK_CONFIGS["dashen"])


def list_available_banks() -> list[dict[str, str]]:
    """List all available bank configurations for demo purposes."""
    return [
        {
            "bank_id": config.bank_id,
            "bank_name": config.bank_name,
            "bank_name_short": config.bank_name_short,
        }
        for config in BANK_CONFIGS.values()
    ]
