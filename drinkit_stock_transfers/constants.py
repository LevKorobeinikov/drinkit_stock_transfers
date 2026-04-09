CODE_CHALLENGE = "OginrRmCZi0dPYB4byweDG3jEVHn-TsMguOvy4vvtF8"
CODE_VERIFIER = "013a3ab5b72bab86077443b492be742a731fc9dad5ea4d03546abfb2"

SCOPES = [
    "openid",
    "incentives",
    "sales",
    "offline_access",
    "email",
    "employee",
    "phone",
    "profile",
    "roles",
    "ext_profile",
    "user.role:read",
    "deliverystatistics",
    "organizationstructure",
    "productionefficiency",
    "orders",
    "production",
    "products",
    "stockitems",
    "accounting",
    "stopsales",
    "staffshifts:read",
    "unitshifts:read",
    "unit:read",
    "shared",
    "marketplacesubscription:read",
    "marketplace",
]

REDIRECT_URL = "https://localhost:5001"
TOKEN_URL = "https://auth.dodois.io/connect/token"

HEADERS_ZERO_SHIPPED = [
    "Точка",
    "Получатель",
    "Накладная",
    "Товар",
    "Заказано",
    "Отгружено",
    "Ожидаемая дата",
]
