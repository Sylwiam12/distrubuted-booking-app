# System rezerwacji i zarządzania miejscami w kinie
### Wstęp
Główną ideą projektu jest realizacja systemu rezerwacji i zarządzania miejscami w kinie. Rozważamy grupę kin zlokalizowanych w Krakowie. Celem systemu jest umożliwienie klientom rezerwacji biletów na pożądany film online.  System umożliwia także zarządzanie seansami i filmami w danych placówkach przez administrację.  
### Wymagania
- system powinien być w stanie wyświetlić listę dostępnych w Krakowie kin,
- użytkownik na początku wybiera lokalizację kina,
- w każdym kinie znajduje się określona liczba sal i w każdej z nich odbywa się jeden seans filmowy,
- istnieje możliwość wyszukiwania filmów po tytule, reżyserze oraz gatunku,
- po wybraniu konkretnego filmu wyświetlany jest krótki opis filmu z uwzględnieniem czasu trwania filmu, języka oraz informacji o dostępności napisów, a także dostępne godziny seansu oraz numer sali,
- po wybraniu godziny seansu klient powinien zostać przekierowany do sekcji rezerwacji biletów, w której widoczny będzie układ miejsc w sali; po wybraniu konkretnego miejsca/miejsc zgodnie z preferencjami będzie możliwa rezerwacja (zakup biletów),
- dostępne i niedostępne miejsca będą wyróżnione kolorami, które będą objaśnione w legendzie,
- system powinien zapewniać, że żaden z dwóch klientów nie może zarezerwować tego samego miejsca,
- przy zakupie biletu wymagane będzie podanie maila oraz imienia i nazwiska,
- bilet zostanie wysłany na podany przy zakupie adres e-mail,
- klienci będą mieć możliwość płacenia kartą,
- dane miejsce jest zarezerwowane przez 30 minut od momentu rozpoczęcia płatności.
### Przypadki użycia - funkcjonalności
![wyszukaj film](https://github.com/Sylwiam12/distrubuted-booking-app/assets/81360507/9f80c509-5d2d-4138-b645-b26132604f1c)
### Analiza systemu
#### Komponenty
System będzie podzielony na kilka komponentów: 
- komponenty dla administracji:
  - komponent do tworzenia filmów,
  - komponent zarządzania godzinami seansów,
  - komponent zarządzania filmami do tworzenia seansów
- komponent dla klientów do rezerwacji miejsc.
#### Baza danych  
![database](https://github.com/Sylwiam12/distrubuted-booking-app/assets/81360507/b2b46b7d-ec99-44cb-acc8-bb47fa20d1cf)
