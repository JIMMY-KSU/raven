# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on August 23, 2017

@author: wangc
"""
from __future__ import division, print_function , unicode_literals, absolute_import
import warnings
warnings.simplefilter('default', DeprecationWarning)

#External Modules------------------------------------------------------------------------------------
import numpy as np
import os
import six
from collections import OrderedDict
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from .PostProcessor import PostProcessor
from utils import utils
from utils import InputData
import Files
import Metrics
#Internal Modules End--------------------------------------------------------------------------------

class Metric(PostProcessor):
  """
    Metrics class.
  """

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    ## This will replace the lines above
    inputSpecification = super(Metrics, cls).getInputSpecification()

    ## TODO: Fill this in with the appropriate tags
    #FeaturesInput = InputData.parameterInputFactory("Features", contentType=InputData.StringType)
    #inputSpecification.addSub(FeaturesInput)
    #TargetsInput = InputData.parameterInputFactory("Targets", contentType=InputData.StringType)
    #inputSpecification.addSub(TargetsInput)
    #MetricInput = InputData.parameterInputFactory("Metric", contentType=InputData.StringType)
    #inputSpecification.addSub(MetricInput)

    return inputSpecification

  def __init__(self, messageHandler):
    """
      Constructor
      @ In, messageHandler, message handler object
      @ Out, None
    """
    PostProcessor.__init__(self, messageHandler)
    self.printTag = 'POSTPROCESSOR Metrics'
    self.dynamic        = False # is it time-dependent?
    self.features       = None  # list of feature variables
    self.targets        = None  # list of target variables
    self.metric         = None  # pointer to a metric
    self.pivotParameter = None
    # assembler objects to be requested
    self.addAssemblerObject('Metric', '1', True)

  def _localWhatDoINeed(self):
    """
      This method is a local mirror of the general whatDoINeed method.
      It is implemented by the samplers that need to request special objects
      @ In , None, None
      @ Out, dict, dictionary of objects needed
    """
    needDict = {'Metrics':[]}
    needDict['Metrics'].append((None, self.metric))
    return needDict

  def _localGenerateAssembler(self,initDict):
    """Generates the assembler.
      @ In, initDict, dict, init objects
      @ Out, None
    """
    metricName = self.metric
    self.metric = initDict['Metrics'][metricName]

  def inputToInternal(self, currentInputs):
    """
      Method to convert an input object into the internal format that is
      understandable by this pp.
      @ In, currentInputs, list or DataObject, data object or a list of data objects
      @ Out, inputDict, dict, current inputs dictionary
    """
    if type(currentInputs) == list:
      currentInput = currentInputs[-1]
    else:
      currentInput = currentInputs

    if len(currentInput) == 0:
      self.raiseAnError(IOError, "The input for ", self.name, " is empty")

    if currentInput.type not in ['PointSet', 'HistorySet']:
      self.raiseAnError(IOError, "Only PointSet and HistorySet are valid! Got ", currentInput.type)

    if currentInput.type == 'PointSet':
      inputDict = {'features':OrderedDict(), 'targets':OrderedDict()}
      for feature in self.features:
        if feature in currentInput.getParaKeys('input'):
          inputDict['features'][feature] = currentInput.getParam('input', feature, nodeId = 'ending').reshape(1,-1)
        elif feature in currentInput.getParaKeys('output'):
          inputDict['features'][feature] = currentInput.getParam('output', feature, nodeId = 'ending').reshape(1,-1)
        else:
          self.raiseAnError(IOError, "Feature ", feature, " has not been found in data object ", currentInput.name)
      if self.targets:
        for target in self.targets:
          if target in currentInput.getParaKeys('input'):
            inputDict['targets'][target] = currentInput.getParam('input', target, nodeId = 'ending').reshape(1,-1)
          elif target in currentInput.getParaKeys('output'):
            inputDict['targets'][target] = currentInput.getParam('output', target, nodeId = 'ending').reshape(1,-1)
          else:
            self.raiseAnError(IOError, "Target ", target, " has not been found in data object ", currentInput.name)
    else:
      self.dynamic = True
      self.raiseAnError(IOError, "Metric can not process HistorySet, because this capability is not implemented yet")

    return inputDict

  def initialize(self, runInfo, inputs, initDict) :
    """
      Method to initialize the pp.
      @ In, runInfo, dict, dictionary of run info (e.g. working dir, etc)
      @ In, inputs, list, list of inputs
      @ In, initDict, dict, dictionary with initialization options
    """
    PostProcessor.initialize(self, runInfo, inputs, initDict)
    self.__workingDir = runInfo['WorkingDir']

  def _localReadMoreXML(self, xmlNode):
    """
      Function to read the portion of the xml input that belongs to this specialized class
      and initialize some stuff based on the inputs
      @ In, xmlNode, xml.etree.ElementTree Element Objects, the xml element node that will be checked against the available options specific to this Sampler
      @ Out, None
    """
    #paramInput = Metric.getInputSpecification()()
    #paramInput.parseNode(xmlNode)

    for child in xmlNode:
      if child.tag == 'Metric':
        if 'type' not in child.attrib.keys() or 'class' not in child.attrib.keys():
          self.raiseAnError(IOError, 'Tag Metric must have attributes "class" and "type"')
        else:
          self.metric = child.text.strip()
      elif child.tag == 'Features':
        self.features = list(var.strip() for var in child.text.split(','))
      elif child.tag == 'Targets':
        self.targets = list(var.strip() for var in child.text.split(','))
      else:
        self.raiseAnError(IOError, "Unknown xml node ", child.tag, " is provided for metric system")
    if not self.features:
      self.raiseAnError(IOError, "XML node 'Features' is required but not provided")
    elif len(self.features) != len(self.targets):
      self.raiseAnError(IOError, 'The number of variables found in XML node "Features" is not equal the number of variables found in XML node "Targets"')

  def collectOutput(self,finishedJob, output):
    """
      Function to place all of the computed data into the output object, (Files or DataObjects)
      @ In, finishedJob, object, JobHandler object that is in charge of running this postprocessor
      @ In, output, object, the object where we want to place our computed results
      @ Out, None
    """
    if finishedJob.getEvaluation() == -1:
      self.raiseAnError(RuntimeError, ' No available output to collect')
    outputDict = finishedJob.getEvaluation()[1]

    if isinstance(output, Files.File):
      availExtens = ['xml', 'csv']
      outputExtension = output.getExt().lower()
      if outputExtension not in availExtens:
        self.raiseAMessage('Metric postprocessor did not recognize extension ".', str(outputExtension), '". The output will be dumped to a text file')
      output.setPath(self.__workingDir)
      self.raiseADebug('Write Metric prostprocessor output in file with name: ', output.getAbsFile())
      output.open('w')
      if outputExtension == 'xml':
        self._writeXML(output, outputDict)
      else:
        separator = ' ' if outputExtension != 'csv' else ','
        self._writeText(output, outputDict, separator)
    else:
      self.raiseAnError(IOError, 'Output type ', str(output.type), ' can not be used for postprocessor', self.name)

  def _writeXML(self,output,outputDictionary):
    """
      Defines the method for writing the post-processor to a .csv file
      @ In, output, File object, file to write to
      @ In, outputDictionary, dict, dictionary stores importance ranking outputs
      @ Out, None
    """
    if output.isOpen():
      output.close()
    if self.dynamic:
      outputInstance = Files.returnInstance('DynamicXMLOutput', self)
    else:
      outputInstance = Files.returnInstance('StaticXMLOutput', self)
    outputInstance.initialize(output.getFilename(), self.messageHandler, path=output.getPath())
    outputInstance.newTree('MetricPostProcessor', pivotParam=self.pivotParameter)
    outputResults = [outputDictionary] if not self.dynamic else outputDictionary.values()
    for ts, outputDict in enumerate(outputResults):
      pivotVal = outputDictionary.keys()[ts]
      for key, value in outputDict.items():
        if len(list(value)) == 1:
          outputInstance.addScalar(key, self.metric.type, value, pivotVal=pivotVal)
        else:
          outputInstance.addVector(key, self.metric.type, value, pivotVal=pivotVal)
    outputInstance.writeFile()

  def _writeText(self,output,outputDictionary, separator=' '):
    """
      Defines the method for writing the post-processor to a .csv file
      @ In, output, File object, file to write to
      @ In, outputDictionary, dict, dictionary stores importance ranking outputs
      @ In, separator, string, optional, separator string
      @ Out, None
    """
    pass

  def run(self, inputIn):
    """
      This method executes the postprocessor action. In this case, it computes all the requested statistical FOMs
      @ In,  inputIn, object, object contained the data to process. (inputToInternal output)
      @ Out, outputDict, dict, Dictionary containing the results
    """
    inputDict = self.inputToInternal(inputIn)
    outputDict = OrderedDict()
    if not self.dynamic:
      for cnt in range(len(self.features)):
        output = self.metric.distance(inputDict['features'][self.features[cnt]], inputDict['targets'][self.targets[cnt]])
        print('output: ', output)
        nodeName = str(self.features[cnt]) + '-' + str(self.targets[cnt])
        outputDict[nodeName] = output
    else:
      self.raiseAnError(IOError, "Not implemented yet")
    return outputDict


  def evaluate(self, estimator, X, y):
    """
      @ In, estimator, instance, the instance of the estimator
      @ In, X, numpy.ndarray, (n_samples, n_features), the training set
      @ In, y, numpy.ndarray, (n_samples,) the target results
      @ Out,
    """
    pass

