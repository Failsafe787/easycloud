# EasyCloud (ALPHA)

|Website|Download|Wiki|Report|License|Issues|
|---------|---------|---------|---------|----------|----------|
| [![Website Button](https://img.shields.io/badge/Open-Website-green.svg)](https://subwave07.github.io/easycloud)| [![Download Button](https://img.shields.io/badge/EasyCloud-0.10.0-blue.svg)](../../archive/master.zip) | [![Wiki Button](../../wiki)] | [![Thesis Button](https://img.shields.io/badge/Report-Italian-yellow.svg)](dummy) | [![GNU v3 License Button](https://img.shields.io/badge/License-GNU%20v3-green.svg)](LICENSE) | [![Report Problems Button](https://img.shields.io/badge/Report-Problems-red.svg)](issues)|


EasyCloud is a text user interface written in Python able to interact with
multiple cloud platforms, such as OpenStack, Amazon Web Services and Google
Cloud Platform. It is based on the [CloudTUI-FTS](https://github.com/mrbuzz/CloudTUI-FTS) project.

With EasyCloud, a user can:  
* start/stop/clone a VM
* manage floating ips and volumes
* monitor the VMs health status
* create/manage policies in order to prevent faults (i.e., "if the CPU utilization is higher than XX %, then clone it")

## Quick start:

1. **Requirements**  
    You need an account for the service you want to use. Certain services
    can charge you for the use of their services, such as Amazon Web Services
    or Google Cloud Platform. Please, consult all the prices listings before
    using EasyCloud.
    Python 3.7 and pip3 19.0 are required in order to use this tool.
    Please note all the tests were conducted on these versions, so it is possible
    that an older or newer version of Python 3 can still run this program.

2. **Install the required core libraries**  
    This step can be done manually or with the installer script provided. In both of the cases, pip3
    must be installed prior to proceeding further.  

    * If you want to use the installer, move to the `EasyCloud/libs_installer` directory and execute

        `./installer.sh` 

        Wait until the end of the process. If an error occourred during the installation, a log file will be
        available in the `libs_installer` directory, containing the cause of failure.

    * If you want to perform a manual installation, open a terminal and run the following command

        `pip3 install --user tzlocal texttable`

3. **Open the file modules/*platform*/settings.cfg and set all the required parameters (API keys, user credentials, etc)**

4. **Optional settings**  
    You can then customize the platform specific settings (if available) in **modules/*platform*/settings.cfg**.
    For example, each platform can have a limited free-tier mode available and this mode must be enable through a variable
    in order to filter certain types of resources, based on the free-tier conditions.  
    Each variable should have a comment explaining its function.

4. **Run EasyCloud** using `easycloud_launcher.sh` on macOS, BSD and GNU/Linux distributions and then following the instruction provided by the tool.
    If a missing package is detected, EasyCloud won't start or will ask if it can be downloaded through pip3, depending on the package.

5. **Flags**  
    CloudTUI shell script can be launched with certain flags, in order to perform the following operations:
    
    * **--debug**  
        save all the outgoing HTTP requests and all the incoming HTTP responses made by Libcloud in `logs/libcloud_debug.log`
        This setting works only if the application has been executed using the shipped shell script.
    
    * **--no_libs_check**  
        disable the dependencies check for each module at the start of EasyCloud

    * **--help**  
         display a list of available flags

    * **--version**  
        display the application version

6. **Debug messages**  
    This application will record all the debug messages in `easycloud.log`, in order to study its behaviour and the Monitor and Rule Engine iterations.

## Wiki

Please, consult the [Wiki](../../wiki) for a more detailed explanation on how to configure EasyCloud.

## Supported platforms

![Platforms logos](README.md_files/providers.jpg)

The following platforms are currently supported by EasyCloud

* **[Amazon Web Services](https://aws.amazon.com)**
* **[Chameleon Cloud](https://www.chameleoncloud.org) (based on Openstack)**
* **[Google Cloud Platform](https://cloud.google.com)**

## Source code download

You can download the application source code from our git repository by using the `git clone <URL>` command,
where `<URL>` has to be replaced with one of the following:

0.10.0 (Preview)(**Current**) - `https://github.com/subwave07/easycloud.git`  
0.08.0 (CloudTUI-FTS, Preview) - `https://github.com/mrbuzz/CloudTUI-FTS.git`  
0.06.0 (CloudTUI-FTS, Preview) - `https://github.com/trampfox/CloudTUI-FTS.git`

## License
This project is available under the GNU General Public License v3. A copy of this license is shipped with the tool and available [here](LICENSE).

## Institute

![University Logo](README.md_files/upo_logo.png)

This project is a collaborative effort made by a group of students of the

**University of Eastern Piedmont Amedeo Avogadro  
Department of Science and Innovation Technology (DiSIT)  
Alessandria and Vercelli, Piedmont, Italy  
[https://www.disit.uniupo.it](https://www.disit.uniupo.it)**

### Author
* Luca Banzato

### Credits
* Andrea Lombardo (for the original CloudTUI project)
* Davide Monfrecola (for the CloudTUI-FTS project)
* Giorgio Gambino (for the CloudTUI-FTS project)
* Irene Lovotti (for the original CloudTUI project)
* Stefano Garione (for the CloudTUI-FTS project)

### Superadvisor
* Massimo Canonico

### Contact info
[massimo.canonico@uniupo.it](mailto:massimo.canonico@uniupo.it)

## Papers

EasyCloud and CloudTUI-FTS have been presented and referenced in the following academic papers:

* **[CloudTUI: a multi Cloud platform Text User Interface](Papers/paper1_cloudtui.pdf)**  
    Canonico M., Lombardo A., Lovotti I.  
    In "7th International Conference on Performance Evaluation Methodologies and Tools, ValueTools '13", pp. 294-297.  
    ICST/ACM  
    2013

* **[CloudTUI-FTS: a user-friendly and powerful tool to manage Cloud Computing Platforms](Papers/paper2_cloudtui.pdf)**  
    Canonico M., Monfrecola D.  
    In "Proceedings of the 9th EAI International Conference on Performance Evaluation Methodologies and Tools", pp. 220-223.  
    ICST (Institute for Computer Sciences, Social-Informatics and Telecommunications Engineering)  
    2016

* **[CIMP: Cloud Integration and Management Platform](Papers/reference1_cloudtui.pdf) (Ref.)**  
    Sefraoui O., Aissaoui M. and Eleuldj M.,
    In "Europe and MENA Cooperation Advances in Information and Communication Technologies", pp. 391-400.  
    Springer, Cham  
    2017
