##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import copy
import functools
import imath

import IECore

import PyOpenColorIO as OCIO

import Gaffer
import GafferUI
import GafferImage
import GafferImageUI

# get default display setup

config = OCIO.GetCurrentConfig()
defaultDisplay = config.getDefaultDisplay()

# add preferences plugs

preferences = application.root()["preferences"]
preferences["displayColorSpace"] = Gaffer.Plug()
preferences["displayColorSpace"]["view"] = Gaffer.StringPlug( defaultValue = config.getDefaultView( defaultDisplay ) )
preferences["displayColorSpace"]["context"] = Gaffer.CompoundDataPlug()

# configure ui for preferences plugs

Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "layout:section", "Display Color Space", persistent = False )

Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["view"], "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget", persistent = False )
for view in config.getViews( defaultDisplay ) :
	Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["view"], str( "preset:" + view ), view, persistent = False )

Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:section", "OCIO Context", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "layout:section:OCIO Context:collapsed", False, persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:widgetType", "GafferImageUI.OpenColorIOTransformUI._ContextFooter", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:index", -1, persistent = False )

# Register with `GafferUI.DisplayTransform` for use by Widgets.

def __processor( display, view ) :

	d = OCIO.DisplayViewTransform()
	d.setSrc( OCIO.ROLE_SCENE_LINEAR )
	d.setDisplay( display )
	d.setView( view )

	context = copy.deepcopy( config.getCurrentContext() )
	gafferContext = Gaffer.Context.current()
	for variable in preferences["displayColorSpace"]["context"] :
		if variable["enabled"].getValue() :
			context[ variable["name"].getValue() ] = gafferContext.substitute( variable["value"].getValue() )

	return config.getProcessor( transform = d, context = context, direction = OCIO.TRANSFORM_DIR_FORWARD )

def __setDisplayTransform() :

	cpuProcessor = __processor( defaultDisplay, preferences["displayColorSpace"]["view"].getValue() ).getDefaultCPUProcessor()

	def f( c ) :

		cc = cpuProcessor.applyRGB( [ c.r, c.g, c.b ] )
		return imath.Color3f( *cc )

	GafferUI.DisplayTransform.set( f )

__setDisplayTransform()

# And connect to `plugSet()` to update `GafferUI.DisplayTransform` again when the user modifies something.

def __plugSet( plug ) :

	if plug.relativeName( plug.node() ) != "displayColorSpace" :
		return

	__setDisplayTransform()

preferences.plugSetSignal().connect( __plugSet, scoped = False )

# Register with `GafferUI.View.DisplayTransform` for use in the Viewer.

def __displayTransformCreator( display, view ) :

	processor = __processor( display, view )
	return GafferImageUI.OpenColorIOAlgo.displayTransformToFramebufferShader( processor )

def __registerViewerDisplayTransforms() :

	for display in config.getDisplays() :
		for view in config.getViews( display ) :
			GafferUI.View.DisplayTransform.registerDisplayTransform(
				f"{display}/{view}",
				functools.partial( __displayTransformCreator, display, view )
			)

__registerViewerDisplayTransforms()

class DisplayTransformPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self.__currentValue = ""

	def _updateFromValues( self, values, exception ) :

		if exception is not None :
			self.__menuButton.setText( "" )
			self.__currentValue = ""
		else :
			assert( len( values ) == 1 )
			self.__currentValue = values[0]
			# Only show the View name, because the Display name is more of
			# a "set once and forget" affair. The menu shows both for when
			# you need to check.
			self.__menuButton.setText( self.__currentValue.partition( "/" )[-1] )

		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		activeViews = Gaffer.Metadata.value( self.getPlug(), "openColorIO:activeViews" ) or "*"

		# View section

		result.append( "/__ViewDivider__", { "divider" : True, "label" : "View" } )

		displayToViews = {}

		currentDisplay, currentView = self.__currentValue.split( "/" )
		for displayTransform in GafferUI.View.DisplayTransform.registeredDisplayTransforms() :
			display, view = displayTransform.split( "/" )
			if not IECore.StringAlgo.matchMultiple( view, activeViews ) :
				continue
			displayToViews.setdefault( display, [] ).append( view )
			if display != currentDisplay :
				continue
			result.append(
				f"/{view}", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), f"{currentDisplay}/{view}" ),
					"checkBox" : view == currentView
				}
			)

		# Display section

		result.append( "/__DisplayDivider__", { "divider" : True, "label" : "Display" } )

		for display, views in displayToViews.items() :
			newValue = "{}/{}".format( display, currentView if currentView in views else views[0] )
			result.append(
				f"/{display}", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), newValue ),
					"checkBox" : display == currentDisplay
				}
			)

		return result

	def __setValue( self, value, unused ) :

		self.getPlug().setValue( value )

GafferImageUI._OpenColorIODisplayTransformPlugValueWidget = DisplayTransformPlugValueWidget
Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "plugValueWidget:type", "GafferImageUI._OpenColorIODisplayTransformPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "userDefault", "{}/{}".format( defaultDisplay, config.getDefaultView( defaultDisplay ) ) )
Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "layout:minimumWidth", 150 )

# Add "Roles" submenus to various colorspace plugs. The OCIO UX guidelines suggest we
# shouldn't do this, but they do seem like they might be useful, and historically they
# have been available in Gaffer. They can be disabled by overwriting the metadata in
# a custom config file.

for node, plug in [
	( GafferImage.ColorSpace, "inputSpace" ),
	( GafferImage.ColorSpace, "outputSpace" ),
	( GafferImage.DisplayTransform, "inputColorSpace" ),
	( GafferImage.ImageReader, "colorSpace" ),
	( GafferImage.ImageWriter, "colorSpace" ),
] :
	Gaffer.Metadata.registerValue( node, plug, "openColorIO:includeRoles", True )
