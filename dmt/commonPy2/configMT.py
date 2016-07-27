# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU Lesser General Public License version 3.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU Lesser General Public License version 3.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               LGPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the LGPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
import os
g_bOnlySubprograms = False
debugParser = False
inputAadlAST = None
verbose = False
showCode = False
args = []
outputDir = "." + os.sep
