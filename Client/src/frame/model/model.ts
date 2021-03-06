/// <reference path="./../../../typings/main.d.ts" />

import $ = require('jquery')
import ko = require('knockout')
import promise = require('ts-promise')
let Promise = promise.Promise

import { Cache } from './Cache'
import { ServerConnector, Relation } from './ServerConnector'

import { Identifiable } from './Interfaces'

export interface UpdateFunc<E extends Identifiable> {
	(obj: E): void
}

export interface Observer<E extends Identifiable> {
	objectAdded: UpdateFunc<E>
	objectRemoved: UpdateFunc<E>
	objectModified: UpdateFunc<E>
}

export interface Filter {
	relation: Relation[]
	attributes: any[]
}

export class Model<E extends Identifiable> {
	cache: Cache<E>
	connection: ServerConnector<E>
	observers: Observer<E>[]

	constructor(type: string, definition: {}, options: {}, parser) {
		this.connection = new ServerConnector(type, definition, options, parser)
		this.cache = new Cache<E>()
		this.observers = []
	}

	public addObserver = (observer: Observer<E>) => {
		this.observers.push(observer)
	}

	public removeObserver = (observer: Observer<E>) => {
		return this.observers.filter((val: Observer<E>, index: number, array: Observer<E>[]) => {
			return observer === val
		})
	}

	public notifyAdded = (obj: E) => {
		for (let observer of this.observers) {
			observer.objectAdded(obj)
		}
	}

	public notifyModified = (obj: E) => {
		for (let observer of this.observers) {
			observer.objectModified(obj)
		}
	}

	public notifyRemoved = (obj: E) => {
		for (let observer of this.observers) {
			observer.objectRemoved(obj)
		}
	}

	public findAll = (config: Filter) => {
		if (config.attributes.length != 0) {
			console.error("attributes filter not implemented yet!!")
		}
		let localObjs = this.cache.retrieveAll()
		if (localObjs.length != 0) {
			return new Promise((resolve, reject) => {
				resolve(localObjs)
			})
		} else {
			return this.connection.getAll(config.relation)
		}
	}

	public findOne = (pin_id: number) => {
		let localPin = this.cache.retrieve(pin_id)
		if (localPin) {
			return new Promise((resolve, reject) => {
				resolve(localPin)
			})
		} else {
			return this.connection.getOne(pin_id)
		}
	}

	public update = (obj: E) => {
		return this.connection.update(obj)
				.then((created: E) => {
			// this.cache.store(obj)
			this.notifyModified(obj)
		})	
	}

	public remove = (obj: E) => {
		return this.connection.remove(obj)
				              .then((removed: E) => {
			// this.cache.remove(removed)
			this.notifyRemoved(removed)
			return removed
		})
	}

	public create = (obj: E, config: Filter) => {
		return this.connection.create(obj, config.relation)
				.then((created: E) => {
			// this.cache.store(created)
			this.notifyAdded(created)
		}, (error) => {
			console.log("error", error)
			throw "Error while adding";
		})
	}
}
