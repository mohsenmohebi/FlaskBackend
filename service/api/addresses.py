import logging

from datetime import date, datetime, timedelta
from os import error

from flask import abort, jsonify
from webargs.flaskparser import use_args

from marshmallow import Schema, fields

from service.server import app, db
from service.models import AddressSegment
from service.models import Person
from dateutil import parser


class GetAddressQueryArgsSchema(Schema):
    date = fields.Date(required=False, missing=datetime.utcnow().date())


class AddressSchema(Schema):
    class Meta:
        ordered = True

    street_one = fields.Str(required=True, max=128)
    street_two = fields.Str(max=128)
    city = fields.Str(required=True, max=128)
    state = fields.Str(required=True, max=2)
    zip_code = fields.Str(required=True, max=10)

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False)


@app.route("/api/persons/<uuid:person_id>/address", methods=["GET"])
@use_args(GetAddressQueryArgsSchema(), location="querystring")
def get_address(args, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    elif len(person.address_segments) == 0:
        abort(404, description="person does not have an address, please create one")

    # Commented by Mohsen
    # address_segment = person.address_segments[-1]
    # return jsonify(AddressSchema().dump(address_segment))

    # added by Mohsen
    address_segments = person.address_segments
    return jsonify(AddressSchema(many=True).dump(address_segments))


@app.route("/api/persons/<uuid:person_id>/address", methods=["PUT"])
@use_args(AddressSchema())
def create_address(payload, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    # If there are no AddressSegment records present for the person, we can go
    # ahead and create with no additional logic.
    elif len(person.address_segments) == 0:
        address_segment = AddressSegment(
            street_one=payload.get("street_one"),
            street_two=payload.get("street_two"),
            city=payload.get("city"),
            state=payload.get("state"),
            zip_code=payload.get("zip_code"),
            start_date=payload.get("start_date"),
            person_id=person_id,
        )

        db.session.add(address_segment)
        db.session.commit()
        db.session.refresh(address_segment)
    else:
        start_date = payload.get("start_date")
        address_segments = person.address_segments
        addresses = AddressSchema(many=True).dump(address_segments)
        skipInsert = False

        for i in range(len(addresses)):
            address = addresses[i]

            # check if the start date exists
            if start_date == parser.parse(str(address["start_date"])).date():
                app.logger.error(
                    "*********************************Please check here***************** "
                )
                app.logger.error(
                    start_date == parser.parse(str(address["start_date"])).date()
                )
                app.logger.error(
                    "*********************************Please check above***************** "
                )
                abort(422, description="address date does exist")
            # check if the address is redundant ..
            if (
                payload.get("street_one") == address["street_one"]
                and payload.get("street_two") == address["street_two"]
                and payload.get("city") == address["city"]
                and payload.get("state") == address["state"]
                and payload.get("zip_code") == address["zip_code"]
            ):

                skipInsert = True
                app.logger.error(f"skipInesrt is: {skipInsert}")
                break

        if not skipInsert:
            address_segment = AddressSegment(
                street_one=payload.get("street_one"),
                street_two=payload.get("street_two"),
                city=payload.get("city"),
                state=payload.get("state"),
                zip_code=payload.get("zip_code"),
                start_date=payload.get("start_date"),
                person_id=person_id,
            )
            db.session.add(address_segment)
            db.session.commit()
            db.session.refresh(address_segment)

    return jsonify(AddressSchema().dump(address_segment))
    # return jsonify(addresses)


@app.route("/api/persons/<uuid:person_id>/address/search", methods=["POST"])
@use_args(AddressSchema())
def get_address_bydate(payload, person_id):
    app.logger.error(
        "*********************************Please check here***************** "
    )
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")

    address_segments = person.address_segments
    addresses = AddressSchema(many=True).dump(address_segments)
    # search_date = payload.get("search_date")
    # app.logger.error("*********************************Please check here***************** ")
    # app.logger.error(str(search_date))
    # app.logger.error("*********************************Please check above***************** ")
    # found_addresses = []
    # for address in addresses:
    #     if search_date == parser.parse(str(address["start_date"])).date():
    #         found_addresses.append(address)
    # found_addresses = filter(lambda x:str(x["start_date"])).date() == search_date,addresses)
    return jsonify(addresses)
