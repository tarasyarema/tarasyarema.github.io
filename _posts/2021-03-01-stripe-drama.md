---
layout: post
title:  "Why using pointers is important"
date:   2021-03-01 11:00:00 +0100
published: true
categories: [programming] 
tags: [go-lang, pointers]
---

## Introduction

Lately at [Capchase](https://capchase.com) we've been working with the [Stripe API](https://stripe.com/docs/api).
The use case can be easily simplified: we need to keep some client data on
our side so that we can operate with it easier than fetching it every time.
For this purpose we use Go, and with it comes all the marshaling and
un-marshaling that we need to handle when working with an API. 

Good to us, Stripe offers a [Go handy package]() to work with the API without having
to handle all the calls manually.
To illustrate this, let's consider that we want to get a specific coupon, for that
we could code the following function

```go
import (
    "github.com/stripe/stripe-go"
    "github.com/stripe/stripe-go/coupon"
)

// We consider that the initial APi key setup has been done
// stripe.Key = "your_stripe_api_key"

// GetCoupon returns the Stripe coupon for the given id
func GetCoupon(id string) (*stripe.Coupon, error) {
    // Set wanted parameters...
    params := &stripe.CouponParams{}
    return coupon.Get(id, params)
}
```

Now, whenever we call `cp, err := GetCoupon(someID)` we will get a Stripe coupon
object `cp`. Now, let's have a look at the [definition of this struct](https://pkg.go.dev/github.com/stripe/stripe-go/v72#Coupon):

```go
// Coupon is the resource representing a Stripe coupon.
// For more details see https://stripe.com/docs/api#coupons.
type Coupon struct {
    APIResource

    // Primitive fields
    AmountOff        int64             `json:"amount_off"`
    Created          int64             `json:"created"`
    Deleted          bool              `json:"deleted"`
    DurationInMonths int64             `json:"duration_in_months"`
    ID               string            `json:"id"`
    Livemode         bool              `json:"livemode"`
    MaxRedemptions   int64             `json:"max_redemptions"`
    Name             string            `json:"name"`
    Object           string            `json:"object"`
    PercentOff       float64           `json:"percent_off"`
    RedeemBy         int64             `json:"redeem_by"`
    TimesRedeemed    int64             `json:"times_redeemed"`
    Valid            bool              `json:"valid"`

    // Non-primitive fields
    AppliesTo        *CouponAppliesTo  `json:"applies_to"`
    Currency         Currency          `json:"currency"`
    Duration         CouponDuration    `json:"duration"`
    Metadata         map[string]string `json:"metadata"`
}
```

Note that I re-ordered the fields so that we have them divided into two groups,
the first one with only _primitive_ type fields, that is numerics, strings and booleans,
and the following with the rest.

## The problem

In particular, when working with Stripe coupons, only one of the fields `AmountOff`
and `PercentOff` may be set. In fact in the official Stripe API docs we can find
this example coupon object

```json
{
  "id": "18OmM8HA",
  "object": "coupon",
  "amount_off": 25,
  "created": 1614605969,
  "currency": "usd",
  "duration": "repeating",
  "duration_in_months": 3,
  "livemode": false,
  "max_redemptions": 10,
  "metadata": {
    "test": "test"
  },
  "name": "25 off",
  "percent_off": null,
  "redeem_by": 1766448000,
  "times_redeemed": 0,
  "valid": true
}
```

Where `percent_off` is not set. The _funny_ part comes when you marshal the Go coupon object,
which would look something like

```json
{
  "id": "18OmM8HA",
  "object": "coupon",
  "amount_off": 25,
  "created": 1614605969,
  "currency": "usd",
  "duration": "repeating",
  "duration_in_months": 3,
  "livemode": false,
  "max_redemptions": 10,
  "metadata": {
    "test": "test"
  },
  "name": "25 off",
  "percent_off": 0, 
  "redeem_by": 1766448000,
  "times_redeemed": 0,
  "valid": true
}
```

**Why we get a `0` in the `percent_off` field?**

## Solution

> TL;DR: Use pointers 🥴

If you have a closer look at the `stripe.Coupon` struct definition we
see that the primitive fields are all non-pointer. Hence, we marshal the
struct `cp` into bytes and look at it we get [zero values](https://golang.org/ref/spec#The_zero_value)
for all those primitive types which were not set initially (`PercentOff`, for instance).

To illustrate this is a really simple environment, have a look at [this playground](https://play.golang.org/p/BDOUlE6RHLH):

```go
package main

import (
    "encoding/json"
    "fmt"
)

type Drama struct {
    Primitive int  `json:"primitive"`
    Ptr       *int `json:"ptr"`
}

func main() {
    // Both fields empty
    d := Drama{}
    b, _ := json.MarshalIndent(d, "", "  ")
    fmt.Println(string(b))
}
```

Which yields the output

```json
{
  "primitive": 0,
  "ptr": null
}
```

With this last example we see that for the end user of the Stripe package it is
_literally impossible_ to know whether the field `PercentOff` was initially empty or not.

## _Postmortem_

When we found the described issue, I immediately created [an issue](https://github.com/stripe/stripe-go/issues/1255) 
in the package repo, and after getting a _better implement your own package_ response
from one of the contributors we decided to fork...

After forking the package repo to our [_pointered_ version of stripe-go](https://github.com/Capchase/stripe-go) I spend a
number of (not few) hours migrating every primitive field of every struct of stripe
to be pointers and making the tests pass... Which end up being much harder than expected
because of a _hidden forgotten channel_ in one of the tests (I may talk about that another day).

![Small commit](/assets/img/stripe-drama-1.PNG)

Finally, we deployed our own version and started using it, which yielded to the wanted results!


If you liked this post [ping me on Twitter](https://twitter.com/voidisomorphism) and... We're hiring! Have a look 
the open positions at Capchase [here](https://www.notion.so/Capchase-Open-Roles-e7ce7acd6a464ee293e38120bac0b526).

