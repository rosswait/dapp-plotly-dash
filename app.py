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
#from memory_profiler import profile
from google.cloud import storage
from dateutil import relativedelta
from dotenv import load_dotenv
from dash.dependencies import Input, Output, State


METADATA_NETWORK_INTERFACE_URL = 'http://metadata.google.internal/computeMetadatnetwork-interfaces/0/ip'

external_js = []

external_css = [
'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css',
# 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.2/css/bootstrap.min.css',
'https://codepen.io/rosswait/pen/NBraqG.css'
]


try:
    r = requests.get(
        METADATA_NETWORK_INTERFACE_URL,
        headers={'Metadata-Flavor': 'Google'},
        timeout=2)
    CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
    gcs = storage.Client()
    bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
    blob = bucket.get_blob("listings_sample.json")
    data = blob.download_as_string(destination_file_name)
    debug = False
    external_js.append('https://www.googletagmanager.com/gtag/js?id=UA-122516304-1')
    external_js.append('https://codepen.io/rosswait/pen/NBraqG.css')

except requests.RequestException:
    data = 'listings_abridged_sample.json'
    debug = True

app = dash.Dash()
server = app.server

for css in external_css:
    app.css.append_css({'external_url': css})

for js in external_js:
    app.scripts.append_script({'external_url': js})

data_types = {
  'listing_start_price_normalized': 'float64',
  'listing_end_price_normalized': 'float64',
  'listing_drop_pct': 'float64',
  'listing_price_delta_normalized': 'float64',
  'resolution_sale_price_normalized': 'float64',
  'resolution_price_delta_normalized': 'float64',
  'resolution_drop_pct': 'float64',
  'duration_hours': 'float64',
  'hours_since_last_listing': 'float64',
  'name': 'category',
  'resolution_event_type': 'category',
  'created_at_trunc': 'datetime',
  'sales_cum': np.float32,
  'listings_cum': np.float32,
  'token_item_id': 'int64',
  'id': 'int64',
  'token_id': np.object_,
  'auction_success_categorical': 'int64',
  'created_at': 'datetime64[ns]',
  'image_url': np.object_,
  'resolution_from_address': np.object_,
  'resolution_to_address': np.object_,
  'event_type': np.object_
}

chunksize=25000

#@profile
def json_chunk_data(path, chunksize, data_types):
  reader = pd.read_json(path, chunksize=chunksize, dtype=data_types, compression='gzip', lines=True)
  graph = pd.concat([x for x in reader], ignore_index=True)
  return graph

graph = json_chunk_data(data,chunksize,data_types)

graph = graph[(graph['duration_hours'] < 10000)
            & (graph['listing_start_price_normalized'] < 400)
            & (graph['listing_start_price_normalized'] >= 0)
            & (graph['listing_start_price_normalized'] > graph['listing_end_price_normalized'])
                ]

names = sorted(list(set(graph['name'])))
name_selection_list = [{'label':name, 'value':name} for name in names]

dimensions = {
  'listing_start_price_normalized': {
    'label': 'Listed Start Price',
    'default_axis_type': 'log',
    'format': ".3f",
    'scatter_rank': 0,
    'inspector_rank':2
  },
  'listing_end_price_normalized': {
    'label': 'Listed End Price',
    'default_axis_type': 'log',
    'format': ".3f",
    'scatter_rank': 1,
    'inspector_rank':3
  },
  'listing_drop_pct': {
    'label': 'Start-End Range (% of Start Price)',
    'format': '%',
    'scatter_rank': 2
  },
  'listing_price_delta_normalized': {
    'label': 'Start-End Range (Absolute)',
    'default_axis_type': 'log',
    'format': ".3f",
    'scatter_rank': 3
  },
  'resolution_sale_price_normalized': {
    'label': 'Sold Price',
    'default_axis_type':'log',
    'format': ".3f",
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'scatter_rank': 4,
    'inspector_rank':4
  },
  'resolution_price_delta_normalized': {
    'label': 'Start-Sold Range (Absolute)',
    'default_axis_type': 'log',
    'format': ".3f",
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'scatter_rank': 5
  },
  'resolution_drop_pct': {
    'label': 'Start-Sold Range (% of Start Price)',
    'format': '%',
    'ineligible_points': ['listed', 'unresolved', 'delisted'],
    'scatter_rank': 6
  },
  'duration_hours': {
    'label': 'Scheduled Duration (Hours)',
    'default_axis_type': 'log',
    'format': ".1f",
    'scatter_rank': 7,
    'inspector_rank':5
  },
  'hours_since_last_listing': {
    'label': 'Hours Since Last Listing',
    'default_axis_type':'log',
    'format': ".2f",
    'scatter_rank': 8,
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

palette = ['rgb(0,31,63, 1)',
'rgba(1,255,112, 1)',
'rgba(46,204,64, 1)',
'rgba(57,204,204, 1)',
'rgba(61,153,112, 1)',
'rgba(127,219,255, 1)',
'rgba(133,20,75, 1)',
'rgba(170,170,170, 1)',
'rgba(177,13,201, 1)',
'rgba(240,18,190, 1)',
'rgba(255,65,54, 1)',
'rgba(255,133,27, 1)',
'rgba(255,220,0, 1)']

palette_name_dict = dict(zip(names, palette))

start_time = dt.datetime(year=2018,month=2, day=1)
end_time = dt.datetime(year=2018,month=6, day=1)
time_slider_interval = relativedelta.relativedelta(end_time, start_time).months

marker_stylings = {
  'default':
    [
      {
      'button_value': 'default',
      'filter_key': 'auction_success_categorical',
      'filter_value': None
      }
    ],
  'success-fail':
  # filter categorical should list unresolved as nan?
    [
      {
        'button_value': 'success-fail',
        'filter_key': 'auction_success_categorical',
        'filter_value': 0,
        'symbol': 'x',
        'size': 7
      },
      {
        'button_value': 'success-fail',
        'filter_key': 'auction_success_categorical',
        'filter_value': 1,
        'symbol': 'circle',
        'size': 6
      }
    ],
  'all-outcomes':
    [
      {
        'button_value': 'all-outcomes',
        'filter_key': 'resolution_event_type',
        'filter_value': 'sold',
        'symbol': 'circle',
        'size': 6,
        'label': 'Sold'
      },
      {
        'button_value': 'all-outcomes',
        'filter_key': 'resolution_event_type',
        'filter_value': 'delisted',
        'symbol': 'x',
        'size': 6,
        'label': 'Delisted'
      },
      {
        'button_value': 'all-outcomes',
        'filter_key': 'resolution_event_type',
        'filter_value': 'listed',
        'symbol': 'triangle-up-open',
        'size': 6,
        'label': 'Re-Listed'
      },
      {
        'button_value': 'all-outcomes',
        'filter_key': 'resolution_event_type',
        'filter_value': 'unresolved',
        'symbol': 'diamond',
        'size': 6,
        'label': 'Active (Unresolved)'
      }
    ]
}

def generate_marker_toggles(maker_stylings):
  marker_toggles = []
  for x in marker_stylings['all-outcomes']:
      y = dict(label=x['label'])
      y['value'] = x['filter_value']
      marker_toggles.append(y)
  return marker_toggles

marker_toggles = generate_marker_toggles(marker_stylings)

def add_months(start_time, months):
  return start_time + relativedelta.relativedelta(months=months)

def generate_url(dapp_name, token_id):
  base_url = 'https://rarebits.io/item'
  dapp_name = dapp_name.replace(' ', '%20')
  token_id = str(int(token_id))
  return base_url+'/'+dapp_name+'/'+token_id

#@profile
def filter_dataframe(df, sample_index, dapp_names, month_slider, outcome_checklist, token_item_id=None, to_address=None, from_address=None):
  if token_item_id is not None:
    df = df.loc[df['token_item_id'] == token_item_id,:]
  if to_address is not None:
    df = df.loc[df['to_address'] == to_address,:]
  if from_address is not None:
    df = df.loc[df['from_address'] == from_address,:]

  # If there's a set of index values in the cache, use it to filter the data
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

def sample_dataframe(df, points_per_series):
  index = []
  for name in names:
      filtered_df = df[df['name'] == name]
      if filtered_df.shape[0] > points_per_series:
          index.extend(list(filtered_df.sample(points_per_series).index))
      else:
          index.extend(filtered_df.index)
  return sorted(index)

def generate_sorted_keys(elements, sort_index):
    keys = [key for key,value in elements.items() if value.get(sort_index, None) is not None]
    ranks = [value[sort_index] for key,value in elements.items() if value.get(sort_index, None) is not None]
    return  [key for (rank,key) in sorted(zip(ranks, keys))]

sorted_axis_keys = generate_sorted_keys(dimensions, 'scatter_rank')
axis_labels = [dict(value=key, label=dimensions[key]['label']) for key in sorted_axis_keys]

sorted_inspector_keys = generate_sorted_keys(dimensions, 'inspector_rank')



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

auction_details_html = html.Div(
  [
    dcc.Graph(
      id='auction-specifics-display'
    ),
    html.Div(
      [
        html.Div(
          [
            html.Div(
              [
                html.P('Only display listings from the selected: '),
                dcc.Checklist(
                  id='auction-detail-freeze',
                  options=[{'label': 'Token Item', 'value': 'token_item_id'},
                           {'label': 'Buyer', 'value': 'to_address'},
                           {'label': 'Seller', 'value': 'from_address'},
                  ],
                  values=[],
                  labelStyle={'display': 'inline-block'}
                )
              ], className='advanced-filter'
            )
          ]
        ),
        html.Div(
          [],
          id='external-link',
          style={'width':400, 'height': 150}#,
          #style={'display': 'inline-block'}
        )
      ],
    ),
  ],
  style={'padding-left': '10',
         'padding-right': '10',
         'padding-top': '10',
         'margin-bottom': '20'#,
         #'background-color': 'rgb(240,234,214)'
  }
)



## Classnames refer to a 12-unit grid that comes from the imported stylesheet

app.layout = html.Div(
  [
    # MAIN HEADING
    html.Div(
      [
          html.H1(
              'Blockchain Digital Good Auctions',
              style={'font-family': 'Helvetica',
                     "margin-top": "10",
                     "margin-bottom": "0"},
              className='eight columns',
          ),
          html.P(
              'Interactive analysis of ERC721 auctions',
              style={'font-family': 'Helvetica',
                     "font-size": "120%",
                     'margin-bottom': 0,
                     'margin-left': 3},
              className='eight columns'
          ),
      ]
      ,className='row'
      ,style={'margin-bottom': 24}
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
                       'margin-top': 10

                       },
                className='label-heading'
            ),
            dcc.Dropdown(
              id='name-picker',
              options=name_selection_list,
              multi=True,
              value=['CryptoBots', 'Ether Tulips'],
              placeholder="Please choose a game"
            )
          ]
          ,className='twelve columns'
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
              style={'margin-top': 12}
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
              id='auction-scatter',
              style={'height': 750}
            )
          ],
          className='seven columns',
          style={'margin-left': 12, 'margin-right': 12}
        ),

        # Auction Details / Scatter Plot
        html.Div(
          [
            dcc.Tabs(
              id='tabs',
              children=[
                dcc.Tab(
                  label='Details Pane',
                  children=[auction_details_html]
                ),
                dcc.Tab(
                  label='Box Plot',
                  children=[boxplot_html]
                )
              ],
              style={'font-family': 'Helvetica'
              },
              content_style={
                'borderLeft': '1px solid #d6d6d6',
                'borderRight': '1px solid #d6d6d6',
                'borderBottom': '1px solid #d6d6d6',
                'padding': '12px'
              }
            ),
          ], className='five columns'
        )
    ],
    style={'margin-top': '24'},
    className='row'
  ),

  html.Div(id='sample-cache', style={'display': 'none'}),
  html.Div(id='selected-listing-cache', style={'display': 'none'})
],className='row'
)


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
    token_item_id = None
    to_address = None
    from_address = None

    if 'token_item_id' in auction_detail_freeze:
      token_item_id = graph.loc[index_id, ['token_item_id']].values[0]

    if 'to_address' in auction_detail_freeze:
      to_address = graph.loc[index_id, ['to_address']].values[0]

    if 'from_address' in auction_detail_freeze:
      from_address = graph.loc[index_id, ['from_address']].values[0]

    filtered_df = filter_dataframe(df=graph, sample_index=sample_index, dapp_names=names, month_slider=month_slider, outcome_checklist=outcome_checklist,
                                   token_item_id=token_item_id, to_address=to_address, from_address=from_address)
    traces = []

    for i, name in enumerate(names):
        df_by_name = filtered_df[filtered_df['name'] == name]
        for j, entry in enumerate(marker_symbols):
          if entry['filter_value'] is None:
            df_by_shape = df_by_name
          else:
            df_by_shape = df_by_name[df_by_name[entry['filter_key']] == entry['filter_value']]
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
            title = 'Plot of Individual Listings',
            hovermode='closest',
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
  filtered_df = filter_dataframe(graph, sample_index, names, month_slider, outcome_checklist)
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

@app.callback(
    dash.dependencies.Output('auction-specifics-display', 'figure'),
    [dash.dependencies.Input('selected-listing-cache', 'children')]
)
def update_auction_detail_table(index_id):
  # Select id of first datapoint in scatter to initialize as a default on pageload
  filtered_df = graph.loc[index_id, sorted_inspector_keys]
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


@app.callback(
    dash.dependencies.Output('external-link', 'children'),
    [dash.dependencies.Input('selected-listing-cache', 'children')]
)
def generate_external_link(index_id):
  name = graph.loc[index_id, ['name']].values[0]
  token_id = graph.loc[index_id, ['token_id']].values[0]
  image_url = graph.loc[index_id, ['image_url']].values[0]
  text = html.Div(
    [
      html.A(
      children=f'View this {name} item on Rarebits.io',
      href= generate_url(name,token_id),
      target= "_blank",
      style={'margin-left': '10', 'vertical-align': 'top'}
      )
    ],
    style={'width': '150','margin-right': '0', 'margin-left': '20', 'display': 'inline-block', 'vertical-align': 'top'}
  )
  image = html.Img(
    src=image_url,
    style={
        'display': 'inline',
        'height': 'inherit',
        'position': 'relative',
        'padding-top': 0,
        'padding-right': 0,
        'margin-bottom': 0
    },
  )
  return [text, image]


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


@app.callback(
    dash.dependencies.Output('outcome-checklist', 'values'),
    [dash.dependencies.Input('outcome-checklist', 'options')])
def set_checkbox_available(available_options):
    foo = [x['value'] for x in available_options if x['disabled'] == False]
    return foo

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

@app.callback(
  dash.dependencies.Output('sample-cache', 'children'),
  [dash.dependencies.Input('sample-size-toggle', 'values')])
def sample_dataset(sample_size_toggle):
  if sample_size_toggle != []:
    sampled_dataframe = sample_dataframe(graph, sample_size_toggle[0])
    return json.dumps(sampled_dataframe)
  else:
    return '{}'

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
