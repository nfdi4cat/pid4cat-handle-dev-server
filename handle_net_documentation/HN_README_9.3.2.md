# CNRI HANDLE.NET® Version 9 Software

HANDLE.NET 9 software is subject to the terms of the Handle.Net Public
License Agreement (version 3).  Please read the license:
https://hdl.handle.net/20.1000/136.

If you are upgrading from an earlier version of the software, see
UPGRADING FROM AN EARLIER VERSION below.  For version 9: BE AWARE that
you must create a backup of the server directory in case you may wish
to downgrade to Handle.Net version 8.1.

NOTE: CNRI no longer supports Handle.Net v6 and older software.

## INSTALLATION

How to Install the Handle.Net (version 9) software:

NOTE: The Handle.Net software should NOT be installed inside a firewall
unless the handle ports (default ports are tcp:2641, tcp:8000, and
udp:2641) are opened for all incoming and outgoing messages.

PLEASE FOLLOW THESE STEPS IN ORDER.

1) Install Java version 8 or greater on your computer.  Note: if Java is
   already on your computer, type 'java -version' at the command prompt to
   find out what version has been installed.

2) Unpack the Handle.Net software distribution into a directory on your
   computer.  For the rest of these instructions, we will assume this
   directory is /hs/handle-9.3.2/.

3) Choose a directory that will hold the configuration and data for
   this server.  For the rest of these instructions we will use the
   /hs/svr_1 directory. Be sure to create a new directory for each
   server on the same machine. To create this directory on unix, run
   this command:
     mkdir -p /hs/svr_1

4) To set up and configure a new or existing server, run the following
   command.

      On Unix-like systems:
        /hs/handle-9.3.2/bin/hdl-setup-server /hs/svr_1

      On Windows systems:
        \hs\handle-9.3.2\bin\hdl-setup-server.bat \hs\svr_1

   Both installation programs will prompt you for your server's IP address
   and the port(s) the server will listen to. By default, the Handle.Net
   software will bind to the following ports:
     TCP: 2641 and 8000
     UDP: 2641

   No other servers should be listening to these ports.

   Be sure to remember the passphrase you used for both the server
   Certification and Administration. You will need the server
   Certification passphrase to start your server and you will need the
   Administration passphrase to load your private key which is
   necessary for authentication when creating and modifying
   identifiers in your service.

5) Once the configuration file has been generated, you will need to
   upload the generated sitebndl.zip file to CNRI's Handle.Net
   Registry ("HNR") Administrator (hdladmin@cnri.reston.va.us). First
   go to <https://hdl.handle.net/20.1000/111> to register to become a
   local handle service provider and then upload your file.  Also
   please read and agree to the Handle.Net Registry Service Agreement
   <https://hdl.handle.net/20.1000/102> and pay the associated fees for
   administration of your prefix.  Note: if you have already
   registered and been allotted a prefix, contact the HNR
   Administrator for instructions on maintaining your existing prefix.

   The HNR Administrator will then create the prefix on the Handle.Net
   Registry (HNR), and notify you when this has been completed.  You
   will not be able to continue the installation until you receive
   further information from the HNR Administrator concerning your
   prefix.

   ONCE YOU RECEIVE THIS PREFIX INFORMATION, THEN PROCEED WITH THE
   FOLLOWING STEPS TO 'HOME' YOUR PREFIX TO YOUR NEW SERVICE.

   **Note:** In the event you decide to enter into a service agreement and
   obtain a prefix from an organization other than CNRI that has been
   authorized and credentialed by the DONA Foundation to provide GHR
   Services, as permitted under section 2(d) of the Handle.Net Public
   License Agreement, then you must comply with the requirements of
   such other organization's service agreement.

6) Go to your svr_1 directory (where you installed the software) and
   edit the config.dct file. Replace the words "YOUR_PREFIX" under
   "server_admins", "replication_admins", and "auto_homed_prefixes"
   with your prefix (as indicated in your email message from the
   Administrator hdladmin@cnri.reston.va.us).  This change allows
   anyone with the private key that matches your public key to be an
   administrator for your identifier and/or resolution services.

7) Start your handle server using the configuration generated in step 4.
   This can be done with the following command:

      On Unix-like systems:
        /hs/handle-9.3.2/bin/hdl-server /hs/svr_1

      On Windows systems:
        \hs\handle-9.3.2\bin\hdl-server.bat \hs\svr_1

   Note: If you chose to encrypt your private key(s), you will be
   prompted for your passphrase here. Also note that Java does not
   have the ability to disconnect from a terminal so you will have to
   put the process in the background. On Unix systems press Ctrl-Z
   then bg then press Enter; you may wish to use the "disown" command
   (or "nohup" or "setsid") to ensure that the process survives the
   end of your terminal session.

   For testing purposes you can use a web browser to connect to your
   server by opening the URL `http://<your-IP-address>:8000/` where
   "your-IP-address" is the address that was entered in the setup
   process.

   **Note:** 'homing' the prefix can now be done by configuration rather than
   by sending a request using the Handle Tool client application.

8) As of version 8.1 a browser-based administration tool is made
   available by the handle server.  In a browser, you can open
   the URL `https://<your-IP-address>:8000/admin` to use the tool.
   The site uses a self-signed certificate by default, which will
   generate a warning and require an explicit permission to visit in
   most browsers.  The page has a "Help" link explaining how to use it.

9) The GUI client Handle Tool can also be used.
   Start the Handle Tool using the following command.

      On Unix-like systems:
        /hs/handle-9.3.2/bin/hdl-admintool

      On Windows systems:
        \hs\handle-9.3.2\bin\hdl-admintool.bat

   Please see the Handle Tool User Manual, included with the software
   distribution, on how to run the tool.

   To create handles, enter the new handle in the Handle Tool and click the
   "Create..." button.  Your authentication information can be your
   public/private key pair that was used for homing your prefix.
   Remember each handle requires an Administrator.

   You can now Add, Edit, and Remove values from the new handle record;
   click "Create Handle" when this is complete.

   For complete documentation on Handle.Net version 9 please refer
   to the Technical Manual (<hdl.handle.net/20.1000/113>).

10) Please send all comments, questions and bug reports to
   hdladmin@cnri.reston.va.us.

## UPGRADING FROM AN EARLIER VERSION

The Handle.Net handle server software has been designed so that new
versions can always be run on existing server directories. Thus it is
always possible to simply:

1) Stop the handle server process.
2) Run the new server software on the same server directory.

If your handle server directory was inside your handle distribution,
you will need to replace the software distribution, even if you keep
the existing server directory.  In particular use the bin/ and lib/
subdirectories of the new software distribution.  Only the server
directory itself should be retained.

Starting with version 7, we have provided a
script 'hdl-server', located in the 'bin' directory of the
distribution, which should be run to start the handle server.  The
script takes a single argument, the handle server directory, for
example "bin/hdl-server existing_server_dir".

(The command used in version 6 to start the handle server will not work,
as multiple Java jar files are now required to run the server.)

Certain configuration changes are recommended however. See below.

- Update the browser-based administration tool to the latest version.

  This is done by default for new server setups. For an existing server:

  1) Create a subdirectory "webapps" if needed in the server directory.
  2) Copy "admin.war" from the software distribution into "webapps".
  Any existing version can simply be overwritten.  This can be done while
  the server is already running the new version of the Handle.Net software.

- Create a backup of the server directory in case you may wish to
  downgrade to Handle.Net version 8.1.

  Handle.Net version 9 upgrades the Berkeley DB JE version for the first
  time in many years.  After running a handle server using Handle.Net
  version 9, the storage directories "bdbje", "replicationDb", and
  "txns", when present, will all be upgraded automatically to the higher
  version format.  After this, it will no longer be possible to open the
  same storage using earlier versions of the Handle.Net software.  If
  you wish to leave open the possibility of downgrading, you should make
  a backup.

- Consider pruning transaction storage.

  By default, the "txns" directory of a Handle server is allowed to grow
  indefinitely.  As of version 9, it is possible to configure the Handle
  server to automatically prune older transactions.  Set property
  "txnlog_num_days_to_keep" in "server_config" in config.dct to be a
  number of days after which remembered transactions will be deleted.
  The default of 0 means to keep forever.  Mirrors which are more than
  the configured number of days out of date will need to redump from
  that primary.

  Previous migration steps given for upgrading to Handle.Net 8.1 are as
  follows. If the handle server is being upgraded from a version earlier
  than 8.1 these steps should be considered as well.

- Ensure the use of BDBJE storage.

  Handle.Net version 6 and previous software defaulted to a built-in storage
  mechanism called JDB which is deprecated in favor of BDBJE. If your
  server directory includes files "handles.jdb" and "nas.jdb" you are
  running the JDB storage; if it includes a subdirectory "bdbje" you are
  running the BDBJE storage. The BDBJE storage offers significantly
  better performance for large numbers of handles. If you are using the
  legacy JDB storage, you can upgrade using the following command (after
  the handle server is stopped):

  - On Unix-like systems: bin/hdl-migrate-storage-to-bdbje /hs/svr_1
  - On Windows systems: bin\hdl-migrate-storage-to-bdbje.bat \hs\svr_1

- Remove "backlog" properties from config.dct.

  Earlier versions of the Handle.net software inserted "backlog"
  properties in config.dct with the value "5". This can be too low for a
  busy server. Remove these properties to use the default, currently 50.

- Convert siteinfo.bin to editable siteinfo.json.

  A handle server's site information is the publicly available
  information used by handle clients to connect to the server. It is
  also used as part of server configuration. Earlier versions used a
  non-human-readable binary format for this file; version 8.1 and later
  prefers a human-readable and human-editable format. To make this
  change, use this command

  - On Unix-like systems: `bin/hdl-convert-siteinfo < /hs/svr_1/siteinfo.bin > /hs/svr_1/siteinfo.json`
  - On Windows systems: `bin\hdl-convert-siteinfo.bat < /hs/svr_1/siteinfo.bin > /hs/svr_1/siteinfo.json`

  Once siteinfo.json is created, you need to delete siteinfo.bin, which
  otherwise takes precedence. Once you have an editable siteinfo.json,
  you can also edit the file to update the "protocolVersion" to "2.10",
  indicating that your server is running version 8.1 or later. You can
  also send your updated siteinfo.json to hdladmin@cnri.reston.va.us ,
  noting your handle prefix, and requesting that the public-facing
  HS_SITE value be updated with the new version information. (This is
  not strictly necessary, as version 8 and later clients can negotiate
  the version; knowing the best version available in advance is an
  optimization.)

- Consider inserting "allow_recursion" = "yes" in the "server_config"
  section of config.dct.

  The old default for the "allow_recursion" server configuration key is
  "yes"; the new default is "no". The "no" is the best choice for handle
  servers which are expected to be asked only for handles for which they
  are responsible. If you use your handle server as a proxy for
  resolving handles at other servers, however, you will need to add
  "allow_recursion" = "yes" to the "server_config" section of
  config.dct. If you're not sure whether you need this, do not add it.

Thank you for your interest in CNRI's Handle.Net software.
