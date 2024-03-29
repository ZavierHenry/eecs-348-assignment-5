# Author(s) names AND netid's:
# Names:            NetIDs:
#   Steven Layne    sol307
#   Amanuel Alemu 	aea592
#   Zavier Henry  	zrh561
# Date: 06/09/2016
# Group work statement: <All group members were
# present and contributing during all work on this project.>
# Description: Best HMM

import xml.dom.minidom
import guid
import math
import os
import random

# A couple contants
CONTINUOUS = 0
DISCRETE = 1
def chunkify(lst,n):
    return [ lst[i::n] for i in xrange(n) ]

class HMM:
    ''' Code for a hidden Markov Model '''

    def __init__(self, states, features, contOrDisc, numVals):
        ''' Initialize the HMM.
            Input:
                states: a list of the hidden state possible values
                features: a list of feature names
                contOrDisc: a dictionary mapping feature names to integers
                    representing whether the feature is continuous or discrete
                numVals: a dictionary mapping names of discrete features to
                    the number of values that feature can take on. '''
        self.states = states 
        self.isTrained = False
        self.featureNames = features
        self.featuresCorD = contOrDisc
        self.numVals = numVals

        # All the probabilities start uninitialized until training
        self.priors = None
        self.emissions = None   #evidence model
        self.transitions = None #transition model

    def train(self, trainingData, trainingLabels):
        ''' Train the HMM on the fully observed data using MLE '''
        print "Training the HMM... "
        self.isTrained = True
        self.trainPriors( trainingData, trainingLabels )
        self.trainTransitions( trainingData, trainingLabels )
        self.trainEmissions( trainingData, trainingLabels ) 
        print "HMM trained"
        print "Prior probabilities are:", self.priors
        print "Transition model is:", self.transitions
        print "Evidence model is:", self.emissions

    def trainPriors( self, trainingData, trainingLabels ):
        ''' Train the priors based on the data and labels '''
        # Set the prior probabilities
        priorCounts = {}
        for s in self.states:
            priorCounts[s] = 0
        for labels in trainingLabels:
            priorCounts[labels[0]] += 1

        self.priors = {}
        for s in self.states:
            self.priors[s] = float(priorCounts[s])/len(trainingLabels)
        

    def trainTransitions( self, trainingData, trainingLabels ):
        ''' Give training data and labels, train the transition model '''
        # Set the transition probabilities
        # First initialize the transition counts
        transitionCounts = {}
        for s in self.states:
            transitionCounts[s] = {}
            for s2 in self.states:
                transitionCounts[s][s2] = 0
                
        for labels in trainingLabels:
            if len(labels) > 1:
                lab1 = labels[0]
                for lab2 in labels[1:]:
                    transitionCounts[lab1][lab2] += 1
                    lab1 = lab2
                    
        self.transitions = {}
        for s in transitionCounts.keys():
            self.transitions[s] = {}
            totForS = sum(transitionCounts[s].values())
            for s2 in transitionCounts[s].keys():
                self.transitions[s][s2] = float(transitionCounts[s][s2])/float(totForS)


    def trainEmissions( self, trainingData, trainingLabels ):
        ''' given training data and labels, train the evidence model.  '''
        self.emissions = {}
        featureVals = {}
        for s in self.states:
            self.emissions[s] = {}
            featureVals[s] = {}
            for f in self.featureNames:
                featureVals[s][f] = []

        # Now gather the features for each state
        for i in range(len(trainingData)):
            oneSketchFeatures = trainingData[i]
            oneSketchLabels = trainingLabels[i]
            
            for j in range(len(oneSketchFeatures)):
                features = oneSketchFeatures[j]
                for f in features.keys():
                    featureVals[oneSketchLabels[j]][f].append(features[f])

        # Do a slightly different thing for conituous vs. discrete features
        for s in featureVals.keys():
            for f in featureVals[s].keys():
                if self.featuresCorD[f] == CONTINUOUS:
                    # Use a gaussian representation, so just find the mean and standard dev of the data
                    # mean is just the sample mean
                    mean = sum(featureVals[s][f])/len(featureVals[s][f])
                    sigmasq = sum([(x - mean)**2 for x in featureVals[s][f]]) / len(featureVals[s][f])
                    sigma = math.sqrt(sigmasq)
                    self.emissions[s][f] = [mean, sigma]
                if self.featuresCorD[f] == DISCRETE:
                    # If the feature is discrete then the CPD is a list
                    # We assume that feature values are integer, starting
                    # at 0.  This assumption could be generalized.
                    counter = 0
                    self.emissions[s][f] = [1]*self.numVals[f]  # Use add 1 smoothing
                    for fval in featureVals[s][f]:
                        self.emissions[s][f][fval] += 1
                    # Now we have counts of each feature and we need to normalize
                    for i in range(len(self.emissions[s][f])):
                        self.emissions[s][f][i] /= float(len(featureVals[s][f])+self.numVals[f])


    def label( self, data):
        ''' Find the most likely labels for the sequence of data
            This is an implementation of the Viterbi algorithm  '''

        priors = self.priors
        trans = self.transitions
        states = self.states

        container = [{state: {"prob": priors[state] * self.getEmissionProb(state, data[0]), "prev": None} for state in states }] #For every state storing probability of that state and the previous state which is none. | Adding in priorprobabilities

        for i in range(1, len(data)): #Running to the length of 1 to the number of observed states
            container.append({}) #Creates a place holder for a new dictionary
            for st in states: #Looks through all possible states
                prev_st = max(states, key=lambda x: container[i-1][x]['prob'] * trans[x][st]) #Iterates over every present key in the dictionary and finds which key has  the maxiumum value for (probability(at that key) * transitive(at that keu))
                max_prob = container[i-1][prev_st]['prob'] * trans[prev_st][st] * self.getEmissionProb(st, data[i]) #Max probability given what the prev_st is
                container[i][st] = {'prob': max_prob, 'prev': prev_st} #Updates the max_probability at the given iteration as well as notes the prev_st that led it to here.

        # Backtrack to find most probable states
        previous = max(container[-1], key=lambda x: container[-1][x]["prob"]) #Finds the most probable previous state
        viterbiStates = [previous] #Adds the state to the viterbi States ordered list

        # Backtrack to find order of states
        for i in range(len(container) - 2, -1, -1):
            viterbiStates.insert(0, container[i + 1][previous]["prev"]) #Inserts the states in orderr
            previous = container[i][previous]["prev"]


                            #### Test Case!!!!!!!!!!!!!!!!!!! Also found at the bottom of this file ####

        # test = HMM(['Sunny','Cloudy', 'Rainy'],['Condition'],DISCRETE, 4)
        # test.priors = {'Sunny': 0.63, 'Cloudy': 0.17, 'Rainy': .20}
        # test.transitions = {'Sunny': {'Sunny': 0.5, 'Cloudy': 0.25, 'Rainy':.25 }, 'Cloudy': {'Sunny': 0.375, 'Cloudy': 0.125, 'Rainy': .375}, 'Rainy': {'Sunny': 0.125, 'Cloudy': 0.675, 'Rainy':.375 }}
        # test.emissions = {'Sunny': {'Condition': [0.6, 0.20, 0.15, .05]}, 'Cloudy': {'Condition': [0.25, 0.25, 0.25, 0.25]}, 'Rainy': {'Condition': [0.05, 0.10, 0.35, 0.50]}}
        # observations = [{'Condition': 0}, {'Condition':2} , {'Condition': 3}]
        # test.featuresCorD = {'Condition': DISCRETE}
        #
        # if (test.label(observations) == ['Sunny', 'Rainy', 'Rainy']):
        #     print "Test Passed"
        # else:
        #     print "Test Failed"

        return viterbiStates #returns the states
    
    def getEmissionProb( self, state, features ):
        ''' Get P(features|state).
            Consider each feature independent so
            P(features|state) = P(f1|state)*P(f2|state)*...*P(fn|state). '''
        #print '\nthis is the state: ', state,'\n'
        prob = 1.0
        for f in features:
            if self.featuresCorD[f] == CONTINUOUS:
                # calculate the gaussian prob
                fval = features[f]
                mean = self.emissions[state][f][0]
                sigma = self.emissions[state][f][1]
                g = math.exp((-1*(fval-mean)**2) / (2*sigma**2))
                g = g / (sigma * math.sqrt(2*math.pi))
                prob *= g
            if self.featuresCorD[f] == DISCRETE:
                fval = features[f]
                prob *= self.emissions[state][f][fval]
                
        return prob
        


class StrokeLabeler:
    def __init__(self):
        ''' Inialize a stroke labeler. '''
        self.labels = ['text', 'drawing']
        # a map from labels in files to labels we use here
        drawingLabels = ['Wire', 'AND', 'OR', 'XOR', 'NAND', 'NOT']
        textLabels = ['Label']
        self.labels = ['drawing', 'text']
        
        self.labelDict = {}
        for l in drawingLabels:
            self.labelDict[l] = 'drawing'
        for l in textLabels:
            self.labelDict[l] = 'text'

        # Define the features to be used in the featurefy function
        # if you change the featurefy function, you must also change
        # these data structures.
        # featureNames is just a list of all features.
        # contOrDisc is a dictionary mapping each feature
        #    name to whether it is continuous or discrete
        # numFVals is a dictionary specifying the number of legal values for
        #    each discrete feature
        self.featureNames = ['length', 'curvature', 'aspect', 'height']
        self.contOrDisc = {'length': DISCRETE, 'curvature': DISCRETE, 'aspect': DISCRETE, 'height': DISCRETE}
        self.numFVals = { 'length': 2, 'curvature': 3, 'aspect': 2, 'height': 2}

        # self.featureNames = ['length','curvature', 'boxArea', 'aspect']
        # self.contOrDisc = {'length': DISCRETE, 'curvature': DISCRETE, 'boxArea': DISCRETE, 'aspect': DISCRETE}
        # self.numFVals = { 'length': 2, 'curvature': 2, 'boxArea': 2, 'aspect': 2}

    def featurefy( self, strokes ):
        ''' Converts the list of strokes into a list of feature dictionaries
            suitable for the HMM
            The names of features used here have to match the names
            passed into the HMM'''
        ret = []
        for s in strokes:
            d = {}  # The feature dictionary to be returned for one stroke

            # If we wanted to use length as a continuous feature, we
            # would simply use the following line to set its value
            #d['length'] = s.length()

            # To use it as a discrete feature, we have to "bin" it, that is
            # we define ranges for "short" (<300 units) and "long" (>=300 units)
            # Short strokes get a discrete value 0, long strokes get
            # discrete value 1.
            # Note that these bins were determined by trial and error, and my
            # looking at the length data, to determine what a good discriminating
            # cutoff would be.  You might choose to add more bins
            # or to change the thresholds.  For any other discrete feature you
            # add, it's up to you to determine how many and what bins you want
            # to use.  This is an important process and can be tricky.  Try
            # to use a principled approach (i.e., look at the data) rather
            # than just guessing.
            l = s.length()
            #d['length'] = l
            if l < 300:
                d['length'] = 0
            else:
                d['length'] = 1

            height = s.topBottom()

            if height > 50:
                d['height'] = 0
            else:
                d['height'] = 1

            boxArea = s.boxArea()


            # if boxArea < 12120.5 - 1000:
            #     d['boxArea'] = 0
            # else:
            #     d['boxArea'] = 1
            # #
            aspect = s.boxAspectRatio()
            #
            if aspect > .5:
                d['aspect'] = 0
            else:
                d['aspect'] = 1
            # #
            if s.sumOfCurvature(abs) < 0.02: # Above the standard deviation
                d['curvature'] = 0
            elif s.sumOfCurvature(abs) < 0.3:
                d['curvature'] = 1
            else:
                d['curvature'] = 2

            # Aspect Ratio Average:  3.13686434228
            # Aspect Ratio Median:  1.03448275862
            # Aspect Ratio Max:  104.5
            # Aspect Ratio Standard Deviation:  6.9336164541

            # Curvature Average:  0.223115424766
            # Curvature Standard Deviation:  0.0942396422484

            # Box Area Average:  58493.0271449
            # Box Area Meadian:  12120.5
            # Box Area Max:  3305737.0
            # Box Standard Deviation:  172129.075146

            # Curvature Area Average:  0.223115424766
            # Curvature Area Meadian:  0.213509314634
            # Curvature Area Max:  0.758175246525
            # Curvature Standard Deviation:  0.0942396422484


            # We can add more features here just by adding them to the dictionary
            # d as we did with length.  Remember that when you add features,
            # you also need to add them to the three member data structures
            # above in the contructor: self.featureNames, self.contOrDisc,
            #    self.numFVals (for discrete features only)


            ret.append(d)  # append the feature dictionary to the list
            
        return ret
    
    def trainHMM( self, trainingFiles ):
        ''' Train the HMM '''
        self.hmm = HMM( self.labels, self.featureNames, self.contOrDisc, self.numFVals )
        allStrokes = []
        allLabels = []
        for f in trainingFiles:
            print "Loading file", f, "for training"
            strokes, labels = self.loadLabeledFile( f )
            allStrokes.append(strokes)
            allLabels.append(labels)
        allObservations = [self.featurefy(s) for s in allStrokes]
        self.hmm.train(allObservations, allLabels)
    def confusion(self, trueLabels, classifications):

        drawingTot = 0.0
        drawingCor = 0.0
        drawingW = 0.0

        textTot = 0.0
        textCor = 0.0
        textW = 0.0

        for i in range(0, len(trueLabels)):
            if trueLabels[i] == 'drawing': #Checks to see if the true label is drawing
                drawingTot += 1.0
                if classifications[i] == 'drawing': #Checks to see if the classification was drawing
                    drawingCor += 1.0 #Successful classification
                else:
                    drawingW += 1 #Failed classification
            if trueLabels[i] == 'text': #checks to see if the true label is text
                textTot += 1.0
                if classifications[i] == 'text': #Checks to see if the classificattion was text
                    textCor += 1.0 #Classification successful
                else:
                    textW += 1.0 #Incorrect classification
        print "True Label \t Classified as Drawing \t Classified as Text \t Percent Correct"
        print "Drawing\t\t\t\t" + str(drawingCor) + "\t\t\t\t\t" + str(drawingW) + "\t\t\t\t" + str(round((drawingCor/drawingTot) * 100, 2)) + " %"
        print "Text\t\t\t\t" + str(textW) + "\t\t\t\t\t" + str(textCor) + "\t\t\t\t" + str(round((textCor/textTot) * 100, 2)) + " %"

        return {'drawing': {'drawing': drawingCor, 'text': drawingW}, 'text': {'drawing': textW, 'text': textCor}}

    def classify(self, trainingDir, numFold):
        '''
        input: Location of training files
        input: Number of desired folds
        Output: Returns the confusion table
        '''

        for fFileObj in os.walk(trainingDir): #Walks through the directory
            lFileList = fFileObj[2]
            break
        goodList = []
        for x in lFileList:
            if not x.startswith('.'):
                goodList.append(x)

        allfiles = [ trainingDir + "/" + f for f in goodList ] #All files present

        vLabels = [] #Viterbi labels1
        rLabels = [] #Real labels

        random.shuffle(allfiles) #Shuffles the files
        subsec = chunkify(allfiles, numFold) #Splits the data into 10 equal parts

        print "Crossfolding...."
        for i in range(numFold):
            print "Crossfold " + str(i + 1) + " results: "
            self.trainHMM([name for index, names in enumerate(subsec) for name in names if index != i]) #Trains with 90 percent of the data
            for test in subsec[i]: #Test with 90 percent of the data
                strokes = self.loadStrokeFile(test)
                vLabels += self.labelStrokes(strokes) #Viterbi produced labels
                rLabels += self.loadLabeledFile(test)[1] #Real labels

        print(self.confusion(rLabels,vLabels)) #Prints the confusion matrix
    def trainHMMDir( self, trainingDir ):
        ''' train the HMM on all the files in a training directory '''
        for fFileObj in os.walk(trainingDir):
            lFileList = fFileObj[2]
            break
        goodList = []
        for x in lFileList:
            if not x.startswith('.'):
                goodList.append(x)
        
        tFiles = [ trainingDir + "/" + f for f in goodList ] 
        self.trainHMM(tFiles)

    def featureTest( self, strokeFile ):
        ''' Loads a stroke file and tests the feature functions '''
        strokes, labels = self.loadLabeledFile( strokeFile )
        for i in range(len(strokes)):
            print " "
            print strokes[i].substrokeIds[0]
            print "Label is", labels[i]
            print "Length is", strokes[i].length()
            print "Curvature is", strokes[i].sumOfCurvature(abs)
    
    def labelFile( self, strokeFile, outFile ):
        ''' Label the strokes in the file strokeFile and save the labels
            (with the strokes) in the outFile '''
        print "Labeling file", strokeFile
        strokes = self.loadStrokeFile( strokeFile )
        labels = self.labelStrokes( strokes )
        print "Labeling done, saving file as", outFile
        self.saveFile( strokes, labels, strokeFile, outFile )

    def labelStrokes( self, strokes ):
        ''' return a list of labels for the given list of strokes '''
        if self.hmm == None:
            print "HMM must be trained first"
            return []
        strokeFeatures = self.featurefy(strokes)
        return self.hmm.label(strokeFeatures)

    def saveFile( self, strokes, labels, originalFile, outFile ):
        ''' Save the labels of the stroke objects and the stroke objects themselves
            in an XML format that can be visualized by the labeler.
            Need to input the original file from which the strokes were read
            so that we can retrieve a lot of data that we don't store here'''
        sketch = xml.dom.minidom.parse(originalFile)
        # copy most of the data, including all points, substrokes, strokes
        # then just add the shapes onto the end
        impl =  xml.dom.minidom.getDOMImplementation()
        
        newdoc = impl.createDocument(sketch.namespaceURI, "sketch", sketch.doctype)
        top_element = newdoc.documentElement

        # Add the attibutes from the sketch document
        for attrib in sketch.documentElement.attributes.keys():
            top_element.setAttribute(attrib, sketch.documentElement.getAttribute(attrib))

        # Now add all the children from sketch as long as they are points, strokes
        # or substrokes
        sketchElem = sketch.getElementsByTagName("sketch")[0]
        for child in sketchElem.childNodes:
            if child.nodeType == xml.dom.Node.ELEMENT_NODE:
                if child.tagName == "point":
                    top_element.appendChild(child)
                elif child.tagName == "shape":
                    if child.getAttribute("type") == "substroke" or \
                       child.getAttribute("type") == "stroke":
                        top_element.appendChild(child)    

        # Finally, add the new elements for the labels
        for i in range(len(strokes)):
            # make a new element
            newElem = newdoc.createElement("shape")
            # Required attributes are type, name, id and time
            newElem.setAttribute("type", labels[i])
            newElem.setAttribute("name", "shape")
            newElem.setAttribute("id", guid.generate() )
            newElem.setAttribute("time", str(strokes[i].points[-1][2]))  # time is finish time

            # Now add the children
            for ss in strokes[i].substrokeIds:
                ssElem = newdoc.createElement("arg")
                ssElem.setAttribute("type", "substroke")
                ssElem.appendChild(newdoc.createTextNode(ss))
                newElem.appendChild(ssElem)
                
            top_element.appendChild(newElem)
            

        # Write to the file
        filehandle = open(outFile, "w")
        newdoc.writexml(filehandle)
        filehandle.close()

        # unlink the docs
        newdoc.unlink()
        sketch.unlink()

    def loadStrokeFile( self, filename ):
        ''' Read in a file containing strokes and return a list of stroke
            objects '''
        sketch = xml.dom.minidom.parse(filename)
        # get the points
        points = sketch.getElementsByTagName("point")
        pointsDict = self.buildDict(points)
    
        # now get the strokes by first getting all shapes
        allShapes = sketch.getElementsByTagName("shape")
        shapesDict = self.buildDict(allShapes)

        strokes = []
        for shape in allShapes:
            if shape.getAttribute("type") == "stroke":
                strokes.append(self.buildStroke( shape, shapesDict, pointsDict ))

        # I THINK the strokes will be loaded in order, but make sure
        if not self.verifyStrokeOrder(strokes):
            print "WARNING: Strokes out of order"

        sketch.unlink()
        return strokes

    def verifyStrokeOrder( self, strokes ):
        ''' returns True if all of the strokes are temporally ordered,
            False otherwise. '''
        time = 0
        ret = True
        for s in strokes:
            if s.points[0][2] < time:
                ret = False
                break
            time = s.points[0][2]
        return ret

    def buildDict( self, nodesWithIdAttrs ):
        ret = {}
        for n in nodesWithIdAttrs:
            idAttr = n.getAttribute("id")
            ret[idAttr] = n
        
        return ret

    def buildStroke( self, shape, shapesDict, pointDict ):
        ''' build and return a stroke object by finding the substrokes and points
            in the shape object '''
        ret = Stroke( shape.getAttribute("id") )
        points = []
        # Get the children of the stroke
        last = None
        for ss in shape.childNodes:
            if ss.nodeType != xml.dom.Node.ELEMENT_NODE \
               or ss.getAttribute("type") != "substroke":
                continue

            # Add the substroke id to the stroke object
            ret.addSubstroke(ss.firstChild.data)
            
            # Find the shape with the id of this substroke
            ssShape = shapesDict[ss.firstChild.data]

            # now get all the points associated with this substroke
            # We'll filter points that don't move here
            for ptObj in ssShape.childNodes:
                if ptObj.nodeType != xml.dom.Node.ELEMENT_NODE \
                   or ptObj.getAttribute("type") != "point":
                    continue
                pt = pointDict[ptObj.firstChild.data]
                x = int(pt.getAttribute("x"))
                y = int(pt.getAttribute("y"))
                time = int(pt.getAttribute("time"))
                if last == None or last[0] != x or last[1] != y:  # at least x or y is different
                    points.append((x, y, time))
                    last = (x, y, time)
        ret.setPoints(points)
        return ret
                

    def loadLabeledFile( self, filename ):
        ''' load the strokes and the labels for the strokes from a labeled file.
            return the strokes and the labels as a tuple (strokes, labels) '''
        sketch = xml.dom.minidom.parse(filename)
        # get the points
        points = sketch.getElementsByTagName("point")
        pointsDict = self.buildDict(points)
    
        # now get the strokes by first getting all shapes
        allShapes = sketch.getElementsByTagName("shape")
        shapesDict = self.buildDict(allShapes)

        strokes = []
        substrokeIdDict = {}
        for shape in allShapes:
            if shape.getAttribute("type") == "stroke":
                stroke = self.buildStroke( shape, shapesDict, pointsDict )
                strokes.append(self.buildStroke( shape, shapesDict, pointsDict ))
                substrokeIdDict[stroke.strokeId] = stroke
            else:
                # If it's a shape, then just store the label on the substrokes
                for child in shape.childNodes:
                    if child.nodeType != xml.dom.Node.ELEMENT_NODE \
                       or child.getAttribute("type") != "substroke":
                        continue
                    substrokeIdDict[child.firstChild.data] = shape.getAttribute("type")

        # I THINK the strokes will be loaded in order, but make sure
        if not self.verifyStrokeOrder(strokes):
            print "WARNING: Strokes out of order"

        # Now put labels on the strokes
        labels = []
        noLabels = []
        for stroke in strokes:
            # Just give the stroke the label of the first substroke in the stroke
            ssid = stroke.substrokeIds[0]
            if not self.labelDict.has_key(substrokeIdDict[ssid]):
                # If there is no label, flag the stroke for removal
                noLabels.append(stroke)
            else:
                labels.append(self.labelDict[substrokeIdDict[ssid]])

        for stroke in noLabels:
            strokes.remove(stroke)
            
        sketch.unlink()
        if len(strokes) != len(labels):
            print "PROBLEM: number of strokes and labels must match"
            print "numStrokes is", len(strokes), "numLabels is", len(labels)
        return strokes, labels

class Stroke:
    ''' A class to represent a stroke (series of xyt points).
        This class also has various functions for computing stroke features. '''
    def __init__(self, strokeId):
        self.strokeId = strokeId
        self.substrokeIds = []   # Keep around the substroke ids for writing back to file
        
    def __repr__(self):
        ''' Return a string representation of the stroke '''
        return "[Stroke " + self.strokeId + "]"

    def addSubstroke( self, substrokeId ):
        ''' Add a substroke Id to the stroke '''
        self.substrokeIds.append(substrokeId)

    def setPoints( self, points ):
        ''' Set the points for the stroke '''
        self.points = points


    # Feature functions follow this line
    def length( self ):
        ''' Returns the length of the stroke '''
        ret = 0
        prev = self.points[0]
        for p in self.points[1:]:
            # use Euclidean distance
            xdiff = p[0] - prev[0]
            ydiff = p[1] - prev[1]
            ret += math.sqrt(xdiff**2 + ydiff**2)
            prev = p
        return ret

    def boxAspectRatio(self): #Height Width Aspect Ratio
        maxX = float(self.points[0][0])
        maxY = float(self.points[0][1])

        minX = float(self.points[0][0])
        minY = float(self.points[0][1])

        for p in self.points[1:]:
            minX = min(minX, float(p[0]))
            maxX = max(maxX, float(p[0]))
            minY = min(minY, float(p[1]))
            maxY = max(maxY, float(p[1]))
        if ((maxY - minY) == 0.0) or ((maxX - minX) == 0.0):
            return 1
        else:
            return (maxY - minY) / (maxX - minX)

    def boxArea(self):

        maxX = float(self.points[0][0])
        maxY = float(self.points[0][1])

        minX = float(self.points[0][0])
        minY = float(self.points[0][1])

        for p in self.points[1:]:
            minX = min(minX, float(p[0]))
            maxX = max(maxX, float(p[0]))
            minY = min(minY, float(p[1]))
            maxY = max(maxY, float(p[1]))

        if ((maxY - minY) is 0) or ((maxX - minX) is 0):
            return 1
        else:
            return (maxY - minY) * (maxX - minX)

    def topBottom(self):
        maxY = float(self.points[0][1])
        minY = float(self.points[0][1])

        for p in self.points[1:]:
            minY = min(minY, float(p[1]))
            maxY = max(maxY, float(p[1]))
        return (maxY - minY)

    def leftRight(self):
        maxX = float(self.points[0][0])
        minX = float(self.points[0][0])

        for p in self.points[1:]:
            minX = min(minX, float(p[1]))
            maxX = max(maxX, float(p[1]))
        return (maxX - minX)

    def sumOfCurvature(self, func=lambda x: x, skip=1):
        ''' Return the normalized sum of curvature for a stroke.
            func is a function to apply to the curvature before summing
                e.g., to find the sum of absolute value of curvature,
                you could pass in abs
            skip is a smoothing constant (how many points to skip)
        '''
        if len(self.points) < 2*skip+1:
            return 0
        ret = 0
        second = self.points[0]
        third = self.points[1*skip]
        for p in self.points[2*skip::skip]:
            
            first = second
            second = third
            third = p
            ax = second[0] - first[0]
            ay = second[1] - first[1]
            bx = third[0] - second[0]
            by = third[1] - second[1]
            
            lena = math.sqrt(ax**2 + ay**2)
            lenb = math.sqrt(bx**2 + by**2)

            dotab = ax*bx + ay*by
            arg = float(dotab)/float(lena*lenb)

            # Fix floating point precision errors
            if arg > 1.0:
                arg = 1.0
            if arg < -1.0:
                arg = -1.0

            curv = math.acos(arg)

            # now we have to find the sign of the curvature
            # get the angle betwee the first vector and the x axis
            anga = math.atan2(ay, ax)
            # and the second
            angb = math.atan2(by, bx)
            # now compare them to get the sign.
            if not(angb < anga and angb > anga-math.pi):
                curv *= -1
            ret += func(curv)

        return ret / len(self.points)

    # You can (and should) define more features here

x = StrokeLabeler()
x.classify("../trainingFiles/", 10) #Training files directory and number of desired folds
#x.trainHMMDir("../trainingFiles/") #../ means go back a directory
#x.labelFile("../trainingFiles/0502_3.9.1.labeled.xml", "results.txt")
#x.labelFile("../trainingFiles/9171_3.8.1.labeled.xml", "results.txt")
#

#### Test Case ####

test = HMM(['Sunny','Cloudy', 'Rainy'],['Condition'],DISCRETE, 4)
test.priors = {'Sunny': 0.63, 'Cloudy': 0.17, 'Rainy': .20}
test.transitions = {'Sunny': {'Sunny': 0.5, 'Cloudy': 0.25, 'Rainy':.25 }, 'Cloudy': {'Sunny': 0.375, 'Cloudy': 0.125, 'Rainy': .375}, 'Rainy': {'Sunny': 0.125, 'Cloudy': 0.675, 'Rainy':.375 }}
test.emissions = {'Sunny': {'Condition': [0.6, 0.20, 0.15, .05]}, 'Cloudy': {'Condition': [0.25, 0.25, 0.25, 0.25]}, 'Rainy': {'Condition': [0.05, 0.10, 0.35, 0.50]}}
observations = [{'Condition': 0}, {'Condition':2} , {'Condition': 3}]
test.featuresCorD = {'Condition': DISCRETE}

if (test.label(observations) == ['Sunny', 'Rainy', 'Rainy']):
    print "Test Passed"
else:
    print "Test Failed"

