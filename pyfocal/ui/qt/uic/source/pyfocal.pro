#-------------------------------------------------
#
# Project created by QtCreator 2015-09-30T22:55:57
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = pyfocal
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    spectrasubwindow.cpp

HEADERS  += mainwindow.h \
    spectrasubwindow.h

FORMS    += mainwindow.ui \
    spectrasubwindow.ui

RESOURCES += \
    icon_resource.qrc \
    qdarkstyle/style.qrc