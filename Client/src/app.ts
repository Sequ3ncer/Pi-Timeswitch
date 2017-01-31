/// <reference path="./../typings/main.d.ts" />

var _ = require('lodash')
import ko = require('knockout')
import router from './router.ts'
import { Model } from './model'

import { Pin, PinJson, pinToJson, jsonToPin } from './model/pin.ts'
import { Sequence, SequenceJson, sequenceToJson, jsonToSequence } from './model/Sequence.ts'

// ************** Setup Router **************

// observable array of current displayed routes
let currentRouteStack = ko.observableArray([])

router.use(function(transition, nextRouteStack){
	// swap next route stack with current stack
	let remove_count = currentRouteStack().length - nextRouteStack.length
	if (remove_count > 0) {
		currentRouteStack.splice(nextRouteStack.length, remove_count)
	}

	for (var _i = 0; _i < nextRouteStack.length; _i++) {
		let new_route = nextRouteStack[_i]

		if (currentRouteStack().length <= _i) {
			// current route stack is shorter 
			currentRouteStack.push(new_route)

		} else if (!_.isEqual(new_route, currentRouteStack()[_i])) {
			// if routes are not equal, replace with new one
			currentRouteStack()[_i] = new_route

			// remove all routes after the current item on current stack
			// stack: [0, ..., _i, ... remove ...]
			if (currentRouteStack().length > _i) {
				let remove_count = currentRouteStack().length -_i -1
				currentRouteStack.splice(_i, remove_count)
			}
		}
	}
})

// ************** Define Model **************

let sequenceDef = {
	start_time: '',
	start_range: '',
	end_time: '',
	end_range: '',
	pin_id: ''
}
let sequenceParser = { 
	jsonToObject: jsonToSequence, 
	objectToJson: sequenceToJson
}
let sequenceModel = new Model<Sequence>('sequence', sequenceDef, {}, sequenceParser)

let pinDef = {
	name: '',
	state: '',
	number: '',
	sequences: {
		jsonApi: 'hasMany',
		type: 'sequences'
	}
}
let pinParser = {
	jsonToObject: jsonToPin,
	objectToJson: pinToJson
}
let pinModel = new Model<Pin>('pin', pinDef, {}, pinParser)


// ************** Register Components **************

ko.components.register('main-page', {
	viewModel: require('./components/main-page/main-page.js'),
	template: require('./components/main-page/main-page.html')
})
ko.components.register('pins-fragment', {
	viewModel: require('./components/pins-fragment/pins-fragment'),
	template: require('./components/pins-fragment/pins-fragment.html')

});
ko.components.register('sequences-fragment', {
	viewModel: require('./components/sequences-fragment/sequences-fragment.ts'),
	template: require('./components/sequences-fragment/sequences-fragment.html')
});

ko.components.register('add-pin-fragment', {
	viewModel: require('./components/add-pin-fragment/add-pin-fragment'),
	template: require('./components/add-pin-fragment/add-pin-fragment.html')
});
ko.components.register('add-sequence-fragment', {
	viewModel: require('./components/add-sequence-fragment/add-sequence-fragment'),
	template: require('./components/add-sequence-fragment/add-sequence-fragment.html')
});

// ************** Set Root ViewModel **************

ko.applyBindings({ 
	routeStack: currentRouteStack, 
	model: {
		sequence: sequenceModel,
		pin: pinModel
	},
	router: router
});
