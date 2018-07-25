# -*- coding: utf-8 -*-
import os
import sys
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly as py
import plotly.graph_objs as go
import pandas as pd
import json
import datetime as dt
import numpy as np
import requests
import dask.dataframe as dd
#from memory_profiler import profile
from google.cloud import storage
from dateutil import relativedelta
from dotenv import load_dotenv
from dash.dependencies import Input, Output, State

#### Load configuration settings

METADATA_NETWORK_INTERFACE_URL = 'http://metadata.google.internal/computeMetadatnetwork-interfaces/0/ip'
CHUNKSIZE=50000
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET', '')
FILE = 'listings_abridged.csv'
PATH = 'gs://' + CLOUD_STORAGE_BUCKET + '/' + FILE


data_types = {
  'listing_start_price_normalized': np.float32,
  'listing_end_price_normalized': np.float32,
  'listing_drop_pct': np.float32,
  'listing_price_delta_normalized': np.float32,
  'resolution_sale_price_normalized': np.float32,
  'resolution_price_delta_normalized': np.float32,
  'resolution_drop_pct': np.float32,
  'duration_hours': np.float32,
  'hours_since_last_listing': np.float32,
  'name': 'category',
  'resolution_event_type': 'category',
  ## Parse this date field with dask instead of declaring
  #'created_at_trunc': 'datetime64[ns]',
  'sales_cum': np.float32,
  'listings_cum': np.float32,
  'token_item_id': np.uint32,
  'id': np.uint32,
  'token_id': np.object_,
  'auction_success_categorical': np.uint8,
  ## Parse this date field with dask instead of declaring
  #'created_at': 'datetime64[ns]',
  'image_url': np.object_,
  'resolution_from_address': np.object_,
  'resolution_to_address': np.object_,
  'event_type': np.object_
}

'''
# Runtime initialization for testing
CLOUD_STORAGE_BUCKET = 'dapp-scatter-dashboard.appspot.com'
FILE = 'listings_abridged.csv'
PATH = 'gs://' + CLOUD_STORAGE_BUCKET + '/' + FILE
debug = True
'''

#### Initialize Runtime Environment

try:
  # Attempt to retrieve Google App engine instance metadata
  r = requests.get(
      METADATA_NETWORK_INTERFACE_URL,
      headers={'Metadata-Flavor': 'Google'},
      timeout=2)
  debug = False
  runtime_prod = True
  # Initialize Google Analytics
  external_js.append('https://www.googletagmanager.com/gtag/js?id=UA-122516304-1')
  external_js.append('https://codepen.io/rosswait/pen/zLBPPg.js')

except requests.RequestException:
    # Overwrite with local filepath if failure
    PATH = 'listings_abridged.csv'
    debug = True
    runtime_prod = False

#### Initialize App

app = dash.Dash()
server = app.server

#### Load external CS & JS

external_js = []
external_css = [
'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css',
'https://codepen.io/rosswait/pen/NBraqG.css'
]

for css in external_css:
    app.css.append_css({'external_url': css})
for js in external_js:
    app.scripts.append_script({'external_url': js})

#### Load remote data into pandas

# For some reason, getting GZIP in the Google Cloud Metadata results in incomplete loading.  Instead access raw & decompress here!
df = dd.read_csv(PATH, dtype=data_types, parse_dates=['created_at', 'created_at_trunc'], compression='gzip',blocksize=None).compute()
df = df.set_index('id')

#### Data cleanup & derivation

# Remove irregular listings
df = df[(df['listing_start_price_normalized'] >= 0)
            & (df['listing_start_price_normalized'] > df['listing_end_price_normalized'])]

# Get list of names
names = sorted(list(set(df['name'])))

start_time = dt.datetime(year=2017,month=6, day=1)
end_time = dt.datetime(year=2018,month=6, day=1)
time_slider_interval = relativedelta.relativedelta(end_time, start_time).months + (relativedelta.relativedelta(end_time, start_time).years * 12)

#### Declare configuration constants

## Dimension metadata (for chart plotting)
# label:             Display label in axis selector and chart axis
# default_axis_type: Default scale in charts
# format:            String formatting
# axis_picker_rank:  Ordinal appearance rank in the axis dropdown
# inspector_rank:    Ordinal appearance rank in the details inspector table

dimensions = {
  'listing_start_price_normalized': {
    'label': 'Listed Start Price',
    'default_axis_type': 'log',
    'format': ".3f",
    'axis_picker_rank': 0,
    'inspector_rank':2
  },
  'listing_end_price_normalized': {
    'label': 'Listed End Price',
    'default_axis_type': 'log',
    'format': ".3f",
    'axis_picker_rank': 1,
    'inspector_rank':3
  },
  'listing_drop_pct': {
    'label': 'Start-End Range (% of Start Price)',
    'format': '%',
    'axis_picker_rank': 2
  },
  'listing_price_delta_normalized': {
    'label': 'Start-End Range (Absolute)',
    'default_axis_type': 'log',
    'format': ".3f",
    'axis_picker_rank': 3
  },
  'resolution_sale_price_normalized': {
    'label': 'Sold Price',
    'default_axis_type':'log',
    'format': ".3f",
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'axis_picker_rank': 4,
    'inspector_rank':4
  },
  'resolution_price_delta_normalized': {
    'label': 'Start-Sold Range (Absolute)',
    'default_axis_type': 'log',
    'format': ".3f",
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'axis_picker_rank': 5
  },
  'resolution_drop_pct': {
    'label': 'Start-Sold Range (% of Start Price)',
    'format': '%',
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'axis_picker_rank': 6
  },
  'duration_hours': {
    'label': 'Scheduled Duration (Hours)',
    'default_axis_type': 'log',
    'format': ".1f",
    'axis_picker_rank': 7,
    'inspector_rank':5
  },
  'hours_since_last_listing': {
    'label': 'Hours Since Last Listing',
    'default_axis_type':'log',
    'format': ".2f",
    'axis_picker_rank': 8,
    'inspector_rank':7
  },
  'name': {
    'label': 'dApp Name',
    'default_axis_type':'log',
    'inspector_rank':0
  },
  'resolution_event_type': {
    'label': 'Auction Resolution',
    'inspector_rank':1
  },
  'created_at_trunc': {
    'label': 'Listed At',
    'inspector_rank':6
  },
  'sales_cum': {
    'label': 'Cumulative Token Sales',
    'inspector_rank':8
  },
  'listings_cum': {
    'label': 'Cumulative Token Listings',
    'inspector_rank':9
  }
}

# Color palette
palette = [
'rgb(0,31,63, 1)',
'rgba(1,255,112, 1)',
'rgba(46,204,64, 1)',
'rgba(255,102,255, 1)',
'rgba(61,153,112, 1)',
'rgba(127,219,255, 1)',
'rgba(133,20,75, 1)',
'rgba(170,170,170, 1)',
'rgba(177,13,201, 1)',
'rgba(240,18,190, 1)',
'rgba(255,65,54, 1)',
'rgba(255,133,27, 1)',
'rgba(255,220,0, 1)']

## Dictionary of metadata for styling scatter-plot marker shapes.
## Each outer dictionary represents a set of dimensions for representing a series of listings
## Each inner dictionary represents a categorical value within a set
# button_value:      Callback value to be passed by this radio button
# df_filter_key:     On which dataframe column to apply the filter
# df_filter_value:   What value in the dataframe to filter
# symbol:            Marker shape in the scatter chart
# size:              Marker size in the scatter chart
# label:             Label (for the checkbox widget)
marker_stylings = {
  'default':
    [
      {
      'button_value': 'default',
      'df_filter_key': 'auction_success_categorical',
      'df_filter_value': None
      }
    ],
  'success-fail':
    [
      {
        'button_value': 'success-fail',
        'df_filter_key': 'auction_success_categorical',
        'df_filter_value': 0,
        'symbol': 'x',
        'size': 7
      },
      {
        'button_value': 'success-fail',
        'df_filter_key': 'auction_success_categorical',
        'df_filter_value': 1,
        'symbol': 'circle',
        'size': 6
      }
    ],
  'all-outcomes':
    [
      {
        'button_value': 'all-outcomes',
        'df_filter_key': 'resolution_event_type',
        'df_filter_value': 'sold',
        'symbol': 'circle',
        'size': 6,
        'label': 'Sold'
      },
      {
        'button_value': 'all-outcomes',
        'df_filter_key': 'resolution_event_type',
        'df_filter_value': 'delisted',
        'symbol': 'x',
        'size': 6,
        'label': 'Delisted'
      },
      {
        'button_value': 'all-outcomes',
        'df_filter_key': 'resolution_event_type',
        'df_filter_value': 'listed',
        'symbol': 'triangle-up-open',
        'size': 6,
        'label': 'Re-Listed'
      },
      {
        'button_value': 'all-outcomes',
        'df_filter_key': 'resolution_event_type',
        'df_filter_value': 'unresolved',
        'symbol': 'diamond',
        'size': 6,
        'label': 'Active (Unresolved)'
      }
    ]
}

#### Declare shared functions

# Uses the "All Outcomes" series in the marker stylings dictionary to generate an array of label/value pairs for the checkbox config.
def generate_marker_toggles(maker_stylings):
  marker_toggles = []
  for x in marker_stylings['all-outcomes']:
      y = dict(label=x['label'])
      y['value'] = x['df_filter_value']
      marker_toggles.append(y)
  return marker_toggles

def add_months(start_time, months):
  return start_time + relativedelta.relativedelta(months=months)

# Generates a link to Rarebits.io from a given token_id & dapp name
def generate_url(dapp_name, token_id):
  base_url = 'https://rarebits.io/item'
  dapp_name = dapp_name.replace(' ', '%20')
  token_id = str(int(token_id))
  return base_url+'/'+dapp_name+'/'+token_id

def filter_dataframe(df, sample_index, dapp_names, month_slider, outcome_checklist, token_item_id=None, to_address=None, from_address=None):
  # Only filter for the values if explicitly passed
  if token_item_id is not None:
    df = df.loc[df['token_item_id'] == token_item_id,:]
  if to_address is not None:
    df = df.loc[df['to_address'] == to_address,:]
  if from_address is not None:
    df = df.loc[df['from_address'] == from_address,:]

  # If there's a set of index values in the browser cache, use it to filter the data.  Used for sampling.
  index = json.loads(sample_index)
  if index != {}:
    df = df.loc[index]

  filtered_df = df[
          df['name'].isin(dapp_names)
          & df['resolution_event_type'].isin(outcome_checklist)
          & (df['created_at'] >= add_months(start_time, month_slider[0]))
          & (df['created_at'] < add_months(start_time, month_slider[1] + 1))
  ]
  return filtered_df

# Return an array of index values representing no more than a fixed number of records per dapp ('name')
def sample_dataframe(df, points_per_series):
  index = []
  for name in names:
      filtered_df = df[df['name'] == name]
      if filtered_df.shape[0] > points_per_series:
          index.extend(list(filtered_df.sample(points_per_series).index))
      else:
          index.extend(filtered_df.index)
  return sorted(index)

# Takes in the 'dimensions' dictionary & the name of a desired sort index (either 'axis_picker_rank' or 'inspector_rank')
# And returns a sorted array of key names (dataframe dimensions)
def generate_sorted_keys(elements, sort_index):
    keys = [key for key,value in elements.items() if value.get(sort_index, None) is not None]
    ranks = [value[sort_index] for key,value in elements.items() if value.get(sort_index, None) is not None]
    return  [key for (rank,key) in sorted(zip(ranks, keys))]

#### Generate Config-Data Mappings

sorted_inspector_keys = generate_sorted_keys(dimensions, 'inspector_rank')
sorted_axis_keys = generate_sorted_keys(dimensions, 'axis_picker_rank')
marker_toggles = generate_marker_toggles(marker_stylings)
palette_name_dict = dict(zip(names, palette))
name_selection_list = [{'label':name, 'value':name} for name in names]
axis_labels = [dict(value=key, label=dimensions[key]['label']) for key in sorted_axis_keys]


#### Initialize HTML for each Tab pane
# Auction details tab
auction_details_html = html.Div(
  [
    # Children to be populated by decorated function
    html.Div(
      [],
      id='external-link'
    ),
    html.Div(
      [
        dcc.Graph(
          id='auction-specifics-display'
        ),
        html.Div(
          [
            html.Div(
              [
                html.P('Freeze scatter ('),
                html.Div(
                  [
                    '  ?  ',
                    html.Span('''These settings will filter the scatterplot to the subset of listings which share the selected characteristic(s)
                                   with the currently highlighted listing.  Enabling any of these options will disable sampling, but you\'ll
                                   still need to manually enable any additional apps you\'d like to be included for a given
                                   owner or seller.'''
                              , className='tooltiptext', style={'padding':'8'}
                              )
                  ],
                  className='tooltip'
                  ,style={'color': 'blue'}
                ),
                html.P(')')
              ],
              style={'color': 'rgb(72, 72, 72)', 'font-weight': 'bold', 'margin-bottom': '2', 'display': 'inline-flex'}
            ),
            html.Div(
              [
                dcc.Checklist(
                  id='auction-detail-freeze',
                  options=[{'label': 'Token Item', 'value': 'token_item_id'},
                           {'label': 'Buyer', 'value': 'to_address'},
                           {'label': 'Seller', 'value': 'from_address'},
                  ],
                  values=[],
                  labelStyle={'display': 'inline-block'}
                )
              ]
            )
          ], style={'flex-direction': 'column', 'padding-left': '15', 'margin-top': '0'}
        )
      ]
    )
  ],
  style={'padding-left': '10',
         'padding-right': '10',
         'padding-top': '10',
         'margin-bottom': '20'
  }
)

#Boxplot tab
boxplot_html = html.Div(
  [
    dcc.Graph(
      id='dapp-boxplot'
    ),
    html.Div(
      [
        dcc.RadioItems(
          id='box-axis-selector',
          options=[
            {'label': 'X Axis', 'value': 'x_axis'
            },
            {'label': 'Y Axis', 'value': 'y_axis'
            }
          ],
        value='x_axis',
        labelStyle={'display': 'inline-block'},
        style={'width': '175%',
               'padding-left': '50'}
        )
      ]
    )
  ]
)


#### Primary HTML body

app.layout = html.Div(
  [
    # MAIN HEADING
    html.Div(
      [
        html.Img(
              src='https://storage.googleapis.com/dapp-scatter-dashboard.appspot.com/ETHEREUM-ICON_Black_small.png',
              style={
                        'margin-right': -15,
                        'margin-left': -15,
                        'margin-top': -5,
                        'height': 85
                    }

            ),
        html.Div(
          [

            html.H1(
                'Blockchain Digital Good Auctions',
                style={'font-family': 'Helvetica', 'margin-bottom': 0}
            ),
            html.P(
                'An interactive analysis of ERC721 auctions',
                style={'font-family': 'Helvetica',
                       "font-size": "120%",
                       'margin-bottom': 0,
                       'margin-left': 3}
            )
          ],
          style={'flex-direction': 'column'
          }
        )
      ]
      ,style={'flex-direction': 'row',
              'display': 'inline-flex',
              'margin-bottom': 24,
              'border-bottom': 'solid 2px #999',
              'width': 744
      }
    ),

    # APP SELECTOR
    html.Div(
      [
        html.Div(
          [
            html.P(
              'Select what apps you want to analyze:',
                style={'font-family': 'Helvetica',
                       'font-weight': 'bold',
                       'margin-bottom': '0px'
                       },
                className='label-heading'
            ),
            dcc.Dropdown(
              id='name-picker',
              options=name_selection_list,
              multi=True,
              value=['CryptoBots', 'CryptoFighters', 'Ether Tulips'],
              placeholder="Please choose a game"
            )
          ]
          ,className='twelve columns'
          ,style={'border': 'solid 2px grey',
          'border-radius': '6px'}
        ),
      ],
      className='row',
      style={'margin-bottom': 24, 'max-width': 744}
    ),

    # X & Y SERIES
    html.Div(
      [
        html.Div(
          [
            html.Div(
              [
                html.P(
                  'X-axis series',
                  style={'font-family': 'Helvetica',
                         'font-weight': 'bold',
                         'margin-bottom': 0},
                  className='label-heading'
                ),
                dcc.Dropdown(
                  id='x-axis-picker',
                  options=axis_labels,
                  multi=False,
                  value='listing_start_price_normalized',
                  className='axis-picker'
                )
              ],
              style={'border': 'solid 2px grey',
              'border-radius': '6px'}
            ),
            html.Div(
              [
                html.P(
                  'Scale',
                  style={'font-family': 'Helvetica',
                         'font-weight': 'bold',
                         'margin-bottom': 0,
                         'color': '#666'}
                ),
                dcc.RadioItems(
                  id='x-axis-scale',
                  options=[
                    {'label': 'Linear', 'value': 'linear'
                    },
                    {'label': 'Log', 'value': 'log'
                    }
                  ],
                value='linear',
                labelStyle={
                  'display': 'inline-block',
                  "margin-left": 12
                }
                ),
              ]
              ,style={
                'margin-top': 2,
                'padding-left': 8,
                'display': 'flex',
                'flex-direction': 'row'
              }
            )
          ]
          ,className='six columns',
          style={'max-width': 360,
                  'display': 'inline-block'
                }

        ),
        html.Div(
          [
            html.Div(
              [
                html.P(
                  'Y-axis series',
                  style={'font-family': 'Helvetica',
                         'font-weight': 'bold',
                         'margin-bottom': 0},
                  className='label-heading'
                ),
                dcc.Dropdown(
                  id='y-axis-picker',
                  options=axis_labels,
                  multi=False,
                  value='listing_drop_pct',
                  className='axis-picker'
                )
              ],
              style={'border': 'solid 2px grey',
              'border-radius': '6px'}
            ),
            html.Div(
              [
                html.P(
                  'Scale',
                  style={'font-family': 'Helvetica',
                         'font-weight': 'bold',
                         'margin-bottom': 0,
                         'color': '#666'}
                ),
                dcc.RadioItems(
                  id='y-axis-scale',
                  options=[
                    {'label': 'Linear', 'value': 'linear'
                    },
                    {'label': 'Log', 'value': 'log'
                    }
                  ],
                value='linear',
                labelStyle={
                  'display': 'inline-block',
                  'padding-left': 24
                }
                ),
              ]
              ,style={
                'margin-top': 2,
                'padding-left': 8,
                'display': 'flex',
                'flex-direction': 'row'
              }
            ),
          ]
          ,className='six columns',
          style={
          'max-width': 360,
          'margin-left': 24
          }
        ),
        html.Div(
          [],
          className='two columns'
        )
      ]
      ,className='row'
      ,style={
        'margin-top': 0,
        'margin-bottom': 24
      }
    ),

    # ADVANCED FILTERS
    html.Details(
      [
        html.Summary('See advanced filters'),
        html.Div(
          [
            html.Div(
              [
                html.P(
                  'Listing Months',
                   style={'font-family': 'Helvetica',
                          'font-weight': 'bold',
                          'margin-right': 8,
                          'width': 160}
                ),
                dcc.RangeSlider(
                  id='month-slider',
                  min=0,
                  max=time_slider_interval,
                  value=[0, time_slider_interval],
                  marks={x: {'label': add_months(start_time,x).strftime("%Y-%m")} for x in range(0,time_slider_interval + 1)},
                  className='range-slider'
                )
              ],
              className='advanced-filter',
              style={'margin-top': 12, 'margin-bottom': 24}
            ),
            html.Div(
              [
                html.P(
                  'Auction Outcomes',
                  style={'margin-right': 8,
                         'font-family': 'Helvetica',
                         'font-weight': 'bold'
                         }
                ),
                dcc.Checklist(
                  id='outcome-checklist',
                  options = marker_toggles,
                  values = [x['value'] for x in marker_toggles],
                  labelStyle={'display': 'inline-block'}
                )
              ]
              ,className='advanced-filter'
            ),
            html.Div(
              [
                html.P(
                  'Scatter Shapes',
                  style={'margin-right': 8,
                         'font-family': 'Helvetica',
                         'font-weight': 'bold'
                         }
                  ),
                dcc.RadioItems(
                  id='marker-symbol-picker',
                  options=[
                    {'label': 'None', 'value':
                      marker_stylings['default']
                    },
                    {'label': 'Success/Failure', 'value':
                      marker_stylings['success-fail']
                    },
                    {'label': 'All Outcomes', 'value':
                      marker_stylings['all-outcomes']
                    }
                    ],
                labelStyle={'display': 'inline-block'},
                value=marker_stylings['default']
                ),
              ]
              ,className='advanced-filter'
            ),
            html.Div(
              [
                html.P(
                  'Sample Limit (per Series):',
                  style={'margin-right': 8,
                         'font-family': 'Helvetica',
                         'font-weight': 'bold'
                         }
                ),
                dcc.Checklist(
                  id='sample-size-toggle',
                  options=[{'label': '100,000', 'value': 100000}],
                  values=[100000],
                  labelStyle={'display': 'inline-block'}
                )
              ], className='advanced-filter'
            )
          ], style={'padding-left': 12,
                    'max-width': 740}
        ),
      ]
      ,className='row'
      ,style={'margin-bottom': '0',
            'padding-bottom': '0'}
    ),

    html.Div(
      [
      # SCATTER PLOT
        html.Div(
          [
            dcc.Graph(
              id='auction-scatter'
            )
          ],
          className='seven columns',
          style={'margin-left': 12, 'margin-right': 12}
        ),

        # Auction Details / Box Plot
        html.Div(
          [
            dcc.Tabs(
              id='tabs',
              children=[
                dcc.Tab(
                  label='Selected Scatter Point Details',
                  children=[auction_details_html],
                  style={'font-weight': 'bold'},
                ),
                dcc.Tab(
                  label='App Comparison Boxplot',
                  children=[boxplot_html],
                  style={'font-weight': 'bold'}
                )
              ],
              style={'font-family': 'Helvetica'
              },
              content_style={
                'borderLeft': '1px solid #d6d6d6',
                'borderRight': '1px solid #d6d6d6',
                'borderBottom': '1px solid #d6d6d6',
                'borderTop': '1px solid #d6d6d6',
                'padding': '12px'
              }
            ),
          ], className='five columns'
        )
    ],
    style={'margin-top': '24', 'margin-bottom': '24'},
    className='row'
  ),
  # FOOTER
  html.Div(
      [
        html.Div(
          [
            html.P(
              'Data courtesy of:'
            , style={'font-weight': 'bold', 'color':'rgb(72, 72, 72)'}),
            html.A(
                'Rarebits.io',
                href='https://rarebits.io/'
            )
          ]
        ),
        html.Div(
          [
            html.P(
              'Code available on:'
              , style={'font-weight': 'bold', 'color':'rgb(72, 72, 72)'}
            ),
            html.A(
                'Github',
                href='https://github.com/rosswait/dapp-plotly-dash'
            )
          ]
        ),
        html.Div(
          [
            html.P(
              'Made with:'
              , style={'font-weight': 'bold', 'color':'rgb(72, 72, 72)'}
            ),
            html.A(
                'Plot.ly',
                href='https://plot.ly/dash/'
            )
          ]
        ),
        html.Div(
          [
            html.P(
              'Created by :'
              , style={'font-weight': 'bold', 'color':'rgb(72, 72, 72)'}
            ),
            html.A(
                'Ross Wait',
                href='https://www.linkedin.com/in/rosswait/'
            )
          ]
        )
      ], style={'display':'flex', 'flex-direction':'row', 'justify-content': 'space-around', 'background-color': '#f9fafd', 'width': '71%'
                ,'margin': 'auto', 'padding': '8px', 'border-radius': '18px', 'border': 'grey solid'}
  ),
  html.Div(id='sample-cache', style={'display': 'none'}),
  html.Div(id='selected-listing-cache', style={'display': 'none'})
],className='row'
)

## Scatterplot

@app.callback(
    dash.dependencies.Output('auction-scatter', 'figure'),
    [
      dash.dependencies.Input('sample-cache', 'children'),
      dash.dependencies.Input('name-picker', 'value'),
      dash.dependencies.Input('marker-symbol-picker', 'value'),
      dash.dependencies.Input('x-axis-picker', 'value'),
      dash.dependencies.Input('y-axis-picker', 'value'),
      dash.dependencies.Input('month-slider', 'value'),
      dash.dependencies.Input('outcome-checklist', 'values'),
      dash.dependencies.Input('x-axis-scale', 'value'),
      dash.dependencies.Input('y-axis-scale', 'value'),
      dash.dependencies.Input('auction-detail-freeze', 'values')
    ],
    [
      dash.dependencies.State('selected-listing-cache', 'children')
    ]
)

def update_scatter(sample_index, names, marker_symbols, x_axis, y_axis, month_slider, outcome_checklist, x_axis_scale, y_axis_scale,
                   auction_detail_freeze, index_id):
    # Filter scatterplot to frozen attributes, if selected
    if 'token_item_id' in auction_detail_freeze:
      token_item_id = df.loc[index_id, ['token_item_id']].values[0]
    else:
       token_item_id = None

    if 'to_address' in auction_detail_freeze:
      to_address = df.loc[index_id, ['to_address']].values[0]
    else:
       to_address = None

    if 'from_address' in auction_detail_freeze:
      from_address = df.loc[index_id, ['from_address']].values[0]
    else:
      from_address = None

    # Primary DF filter
    filtered_df = filter_dataframe(df=df, sample_index=sample_index, dapp_names=names, month_slider=month_slider, outcome_checklist=outcome_checklist,
                                   token_item_id=token_item_id, to_address=to_address, from_address=from_address)
    traces = []

    # Plot individual traces for each dapp name and auction outcome dimension (if applicable)
    for i, name in enumerate(names):
        df_by_name = filtered_df[filtered_df['name'] == name]
        for j, entry in enumerate(marker_symbols):
          if entry['df_filter_value'] is None:
            df_by_shape = df_by_name
          else:
            df_by_shape = df_by_name[df_by_name[entry['df_filter_key']] == entry['df_filter_value']]
          trace = go.Scattergl(
                  x = df_by_shape[x_axis],
                  y = df_by_shape[y_axis],
                  mode = 'markers',
                  name = name,
                  legendgroup = name,
                  showlegend = False if j != 0 else True,
                  customdata = df_by_shape.index,
                  selected = dict(
                    marker = dict(
                      size = 10,
                      color = 'black'
                    )
                  ),
                  marker = dict(
                      symbol = entry.get('symbol','circle'),
                      opacity = 0.85,
                      size = entry.get('size', 6),
                      color = palette_name_dict[name],
                      line = dict(
                          width = 1,
                          color = entry.get('line_color', 'rgb(153, 153, 153)')
                      )
                  )
                )
          traces.append(trace)

    layout = go.Layout(
            title = 'Scatter Plot of Individual Listings',
            hovermode='closest',
            height=598.5,
            xaxis=dict(
             type= x_axis_scale,
             title= dimensions[x_axis]['label'],
             showspikes=True,
             spikecolor='rgba(153, 153, 153, 0.35)',
             tickformat=dimensions[x_axis].get('format', '~g'),
             hoverformat =dimensions[x_axis].get('format', '.2f'),
             dtick= 1 if x_axis_scale == 'log' else None
            ),
            yaxis=dict(
              type= y_axis_scale,
              title= dimensions[y_axis]['label'],
              showspikes=True,
              spikecolor='rgba(153, 153, 153, 0.35)',
              tickformat=dimensions[y_axis].get('format', '~g'),
              hoverformat =dimensions[y_axis].get('format', '.2f'),
              dtick= 1 if y_axis_scale == 'log' else None
            ),
            legend=dict(
              x= -0.1,
              y= 1.05,
              orientation='h'
            ),
            margin=dict(
              l= 30,
              r= 20
            )
        )

    return  {
        'data': traces,
        'layout': layout
      }

## Boxplot

@app.callback(
    dash.dependencies.Output('dapp-boxplot', 'figure'),
    [
      dash.dependencies.Input('sample-cache', 'children'),
      dash.dependencies.Input('name-picker', 'value'),
      dash.dependencies.Input('month-slider', 'value'),
      dash.dependencies.Input('outcome-checklist', 'values'),
      dash.dependencies.Input('x-axis-picker', 'value'),
      dash.dependencies.Input('y-axis-picker', 'value'),
      dash.dependencies.Input('box-axis-selector', 'value'),
      dash.dependencies.Input('x-axis-scale', 'value'),
      dash.dependencies.Input('y-axis-scale', 'value')
    ])

def update_boxplot(sample_index, names, month_slider, outcome_checklist, x_axis, y_axis, box_axis_selector, x_axis_scale, y_axis_scale):
  filtered_df = filter_dataframe(df, sample_index, names, month_slider, outcome_checklist)
  traces = []

  for name in names:
    axis = x_axis if box_axis_selector == 'x_axis' else y_axis
    axis_scale = x_axis_scale if box_axis_selector == 'x_axis' else y_axis_scale
    trace = go.Box(
      y=filtered_df[filtered_df['name'] == name][axis],
      boxpoints='outliers',
      marker=dict(#color=palette_name_dict[name],
                  line=dict(outliercolor='rgb(153, 153, 153)')
                  ),
      line=dict(color='rgb(153, 153, 153)'),
      fillcolor=palette_name_dict[name],
      name=name
      )
    traces.append(trace)

  layout = go.Layout(
    title = f'Boxplot ({dimensions[axis]["label"]})',
    hoverlabel = dict(
      bgcolor = 'rgba(153, 153, 153, 0.35)'
      ),
    yaxis = dict(
      type = axis_scale,
      tickformat=dimensions[axis].get('format', '~g'),
      hoverformat =dimensions[axis].get('format', '.2f'),
      dtick= 1 if axis_scale == 'log' else None
      ),
    margin=dict(
      t=30,
      b=0
      )
    )

  return {'data':traces,
          'layout':layout
  }

## This function updates a hidden Div to contain the index ID of the most-recently-clicked marker in the scatterplot

@app.callback(
    dash.dependencies.Output('selected-listing-cache', 'children'),
    [dash.dependencies.Input('auction-scatter', 'clickData'),
     dash.dependencies.Input('auction-scatter', 'figure')
     ]
)
def update_selected_listing_cache(click_data, figure):
  if click_data is None:
    index_id = figure['data'][0]['customdata'][0]
  else:
    index_id = click_data['points'][0]['customdata']
  return index_id

# This function draws the auction details table, which contains information about the most recently clicked scatter marker

@app.callback(
    dash.dependencies.Output('auction-specifics-display', 'figure'),
    [dash.dependencies.Input('selected-listing-cache', 'children')]
)
def update_auction_detail_table(index_id):
  # Select id of first datapoint in scatter to initialize as a default on pageload
  filtered_df = df.loc[index_id, sorted_inspector_keys]
  dapp_color = palette_name_dict[filtered_df['name']]

  traces = []
  trace = go.Table(
    header = dict(
      values = ["<b>Auction Details</b>", "<b>Value</b>"],
      line = dict(color='#7D7F80'),
      fill = dict(color=(dapp_color.replace('1)', '0.6)'))),
      align = ['left'] * 5,
      font = dict(family = 'Helvetica',
                  size = 16)
      ),
    cells = dict(
      values = [ # Left Column
                [dimensions[key]['label'] for key in sorted_inspector_keys],
                 # Right Column
                filtered_df.values],
       line = dict(color='#7D7F80'),
       fill = dict(color='rgb(247, 248, 249)'),
       align = ['left', 'center'] * 5,
       height = 25,
       format = [  # Left Column
                  ['' for value in sorted_inspector_keys],
                   # Right Column
                  [dimensions[key].get('format', None) for key in sorted_inspector_keys]
                ],
       font = dict(family = 'Helvetica',
                  size = 12))
  )

  layout = go.Layout(
    margin=dict(
      b=0,
      t=10,
      l=10,
      r=10
      ),
    height=315
  )

  traces.append(trace)

  return {'data': traces, 'layout': layout}

# This function generates the 'external listing pane' from the current listing selection cache.
# It renders a link to Rarebits.IO, as well as an externally hosted image URL, within an HTML Div.

@app.callback(
    dash.dependencies.Output('external-link', 'children'),
    [dash.dependencies.Input('selected-listing-cache', 'children')]
)
def generate_external_link(index_id):
  name = df.loc[index_id, ['name']].values[0]
  token_id = df.loc[index_id, ['token_id']].values[0]
  image_url = df.loc[index_id, ['image_url']].values[0]
  output = html.A(
    [
      html.Div(
        [
          html.Div(
            [
              html.Span(f'Details for this {name} item',
                  style={'color': '#484848', 'font-size': '16', 'font-weight': 'bold', 'position': 'relative', 'bottom': '-13'}
              ),
              html.Span('(click to view on Rarebits.io)',
                  style={'color': 'blue', 'font-size': '10', 'display': 'block', 'position': 'relative', 'bottom': '-13'})
            ], style = {'width': '140', 'margin-top': '4'}
          ),
          html.Img(
            src=image_url,
            style={
                'display': 'inline',
                'height': 'inherit',
                'max-height': 100,
                'position': 'relative',
                'padding-top': 0,
                'padding-right': 0,
                'margin-bottom': 0
            },
          )
        ],
        style={'flex-direction': 'row',
              'height': 'inherit',
              'display': 'flex',
              'justify-content': 'space-around',
              'border': '2px grey dotted',
              'background-color': '#e9e9e97a'
        }
      )
    ],
    href= generate_url(name,token_id),
    target= "_blank",
    style={'height': 'inherit',
           'text-decoration': 'none'}
  )
  return output

# This function deactivates some irrelevant auction outcomes from the selection element.
# For example, selecting "Sold Price" as an axis will remove unsold listings from the dataset and selector

@app.callback(
  dash.dependencies.Output('outcome-checklist', 'options'),
  [dash.dependencies.Input('marker-symbol-picker', 'value'),
   dash.dependencies.Input('x-axis-picker', 'value'),
   dash.dependencies.Input('y-axis-picker', 'value')])
def set_checkbox_options(marker_symbols, x_axis, y_axis):
    result = []

    for value in marker_toggles:
      if ((marker_symbols[0]['button_value'] == 'success-fail') & (value['value'] == 'unresolved')):
        value['disabled'] = True
      elif value['value'] in dimensions[x_axis].get('ineligible_points',[]) + dimensions[y_axis].get('ineligible_points',[]):
        value['disabled'] = True
      else:
        value['disabled'] = False
      result.append(value)
    return result

# Any options disabled from the selection checklist also have their values removed

@app.callback(
    dash.dependencies.Output('outcome-checklist', 'values'),
    [dash.dependencies.Input('outcome-checklist', 'options')])
def set_checkbox_available(available_options):
    foo = [x['value'] for x in available_options if x['disabled'] == False]
    return foo

# Log/linear scale toggle inherits default value upon dimension selection

@app.callback(
  dash.dependencies.Output('x-axis-scale', 'value'),
  [dash.dependencies.Input('x-axis-picker', 'value')])
def set_checkbox_options(x_axis):
    return dimensions[x_axis].get('default_axis_type', 'linear')

@app.callback(
  dash.dependencies.Output('y-axis-scale', 'value'),
  [dash.dependencies.Input('y-axis-picker', 'value')])
def set_checkbox_options(y_axis):
    return dimensions[y_axis].get('default_axis_type', 'linear')

# If the "Sample Series" setting is selected, send a JSON list of sampled index values to a hidden Div in the browser
# If unselected, send an empty JSON list

@app.callback(
  dash.dependencies.Output('sample-cache', 'children'),
  [dash.dependencies.Input('sample-size-toggle', 'values')])
def sample_dataset(sample_size_toggle):
  if sample_size_toggle != []:
    sampled_dataframe = sample_dataframe(df, sample_size_toggle[0])
    return json.dumps(sampled_dataframe)
  else:
    return '{}'

# If any of the "freeze" options are selected from the auction details pane, automatically disable series sampling
# If those options are disabled, re-enable sampling

@app.callback(
  dash.dependencies.Output('sample-size-toggle','values'),
  [dash.dependencies.Input('auction-detail-freeze', 'values')])
def remove_sample_restriction(auction_detail_freeze):
  if auction_detail_freeze == []:
    return [100000]
  else:
    return []

if __name__ == '__main__':
    app.run_server(debug=debug)
