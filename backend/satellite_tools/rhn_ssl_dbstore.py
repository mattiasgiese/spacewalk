#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
# 
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation. 
#

import os
import sys
from optparse import Option, OptionParser

from common import rhnTB
from common.rhnConfig import CFG, initCFG
from server import rhnSQL

import satCerts

DEFAULT_TRUSTED_CERT = 'RHN-ORG-TRUSTED-SSL-CERT'

def fetchTraceback(method=None, req=None, extra=None):
    """ a cheat for snagging just the string value of a Traceback
        NOTE: this tool may be needed for RHN Satellite 3.2 as well,
              which doesn't have a fetchTraceback. So... this if for
              compatibility.
    """
    from cStringIO import StringIO
    exc = StringIO()
    rhnTB.Traceback(method=method, req=req, mail=0, ostream=exc,
                    extra=extra, severity=None)
    return exc.getvalue()

def processCommandline():
    initCFG('server.satellite')
    
    options = [
        Option('--ca-cert',      action='store', default=DEFAULT_TRUSTED_CERT, type="string", help='public CA certificate, default is %s' % DEFAULT_TRUSTED_CERT),
        Option('--label',        action='store', default='RHN-ORG-TRUSTED-SSL-CERT', type="string", help='FOR TESTING ONLY - alternative database label for this CA certificate, default is "RHN-ORG-TRUSTED-SSL-CERT"'),
        Option('-v','--verbose', action='count', help='be verbose (accumulable: -vvv means "be *really* verbose").'),
              ]

    values, args = OptionParser(option_list=options).parse_args()

    # we take no extra commandline arguments that are not linked to an option
    if args:
        msg = ("ERROR: these arguments make no sense in this context (try "
               "--help): %s\n" % repr(args))
        raise ValueError(msg)

    if not os.path.exists(values.ca_cert):
        sys.stderr.write("ERROR: can't find CA certificate at this location: "
                         "%s\n" % values.ca_cert)
        sys.exit(10)

    try:
        db_backend = CFG.DB_BACKEND
        db_host = CFG.DB_HOST
        db_port = CFG.DB_PORT
        db_user = CFG.DB_user
        db_password = CFG.DB_PASSWORD
        db_name = CFG.DB_NAME

        rhnSQL.initDB(backend=db_backend, host=db_host, port=db_port,
                    username=db_user, password=db_password, database=db_name)
    except:
        sys.stderr.write("""\
ERROR: there was a problem trying to initialize the database:

%s\n""" % fetchTraceback())
        sys.exit(11)

    if values.verbose:
        print 'Public CA SSL certificate:  %s' % values.ca_cert
        
    return values


#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    """ main routine
        10  CA certificate not found
        11  DB initialization failure
        12  no Organization ID. Something very bad is going on.
        13  Couldn't insert the certificate for whatever reason.
    """

    values = processCommandline()

    def writeError(e):
        sys.stderr.write('\nERROR: %s\n' % e)

    try:
        satCerts.store_rhnCryptoKey(values.label, values.ca_cert, verbosity=values.verbose)
    except satCerts.NoOrgIdError, e:
        writeError("no organization ID!?!\n\n%s\n" % fetchTraceback())
        sys.exit(12)
    except satCerts.CaCertInsertionError, e:
        writeError("no organization ID!?!\n\n%s\n" % fetchTraceback())
        sys.exit(13)
    return 0

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.stderr.write('\nWARNING: intended to be wrapped by another executable\n'
                     '           calling program.\n')
    sys.exit(main() or 0)
#===============================================================================


