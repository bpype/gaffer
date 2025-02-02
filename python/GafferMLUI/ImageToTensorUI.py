##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferML

Gaffer.Metadata.registerNode(

	GafferML.ImageToTensor,

	"description",
	"""
	Converts images to tensors for use with the Inference node.

	> Note : Only the data window is converted, as it would typically be
	> wasteful to convert and process the empty pixels outside the data window.
	> If this is necessary, merge the image over a Constant image before
	> conversion.
	""",

	plugs = {

		"image" : [

			"description",
			"""
			The image to be converted.
			""",

		],

		"view" : [

			"description",
			"""
			The image view to take the tensor data from.
			""",

			"plugValueWidget:type", "GafferImageUI.ViewPlugValueWidget",

			"noduleLayout:visible", False,

		],

		"channels" : [

			"description",
			"""
			The list of channels to convert. Channels are added to the
			tensor in the order specified, so can be shuffled by changing
			the order. For example, an order of `[ "B", "G", "R" ]` might
			be needed for use with models trained on images using OpenCV
			conventions.
			""",

			"noduleLayout:visible", False,

		],

		"interleaveChannels" : [

			"description",
			"""
			Interleaves the channel data, so that all channels for a single
			pixel are adjacent in memory. Whether or not this is needed depends
			on the input requirements of the model the tensor is used with.
			""",

			"noduleLayout:visible", False,

		],

		"tensor" : [

			"description",
			"""
			The output tensor.
			""",

			"layout:visibilityActivator", lambda plug : False,

		],

	}
)
