create schema AutomaticBeerTap collate utf8mb4_general_ci;
use AutomaticBeerTap;

create or replace table beer
(
    name            varchar(50) charset utf8mb3 not null
        primary key,
    style           varchar(50)                 not null,
    abv             decimal(2, 1)               not null,
    ebc             decimal(3, 1)               not null,
    ibu             int(2)                      not null,
    kcal            decimal(3, 1)               not null comment 'kcal per 100ml',
    price_per_liter decimal(3, 2)               not null
);

create or replace table glass
(
    rfid    bigint        not null
        primary key,
    volume  decimal(3, 2) not null comment 'Volume of fluid liters',
    balance decimal(5, 2) not null,
    constraint glass_rfid_uindex
        unique (rfid)
);

create or replace table keg
(
    id                int auto_increment
        primary key,
    beer              varchar(50) charset utf8mb3 not null,
    valve_id          int(2)                      null,
    volume            int(2)                      not null,
    pressure          decimal(3, 2)               not null,
    remaining_content decimal(4, 2)               not null,
    constraint keg_id_uindex
        unique (id),
    constraint keg_ibfk_1
        foreign key (beer) references beer (name)
);

create or replace index beerId
    on keg (beer);

create or replace table pour
(
    id        int auto_increment
        primary key,
    keg       int      not null,
    glass     bigint   not null,
    timestamp datetime not null,
    constraint pour_id_uindex
        unique (id),
    constraint pour_glass_fk
        foreign key (glass) references glass (rfid),
    constraint pour_keg_fk
        foreign key (keg) references keg (id)
);

CREATE USER 'automaticBeerTap'@'%' IDENTIFIED BY 'xUyQ557BcHjMEByu';
GRANT ALL PRIVILEGES ON AutomaticBeerTap.* TO 'automaticBeerTap'@'%';
FLUSH PRIVILEGES;

