import asyncio
import pandas as pd
import plotly.graph_objects as go

async def standard_pie_chart(values, names, title, path, filename):
    # Create a DataFrame
    df = pd.DataFrame({'Role': names, 'Count': values})

    # Sort the DataFrame by 'Count' column in descending order
    df = df.sort_values(by='Count', ascending=False)

    # Limit the DataFrame to only top roles and combine others into a single category
    top_roles_count = 10
    if len(df) > top_roles_count:
        other_roles_count = df['Count'][top_roles_count:].sum()
        df = df[:top_roles_count]
        df.loc[len(df)] = ['Other roles', int(other_roles_count)]

    # Create the Pie chart
    fig = go.Figure(go.Pie(labels=df['Role'], values=df['Count']))

    # Update trace properties
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=1)),
        textinfo='percent+value',
        textfont=dict(color='white', size=12, family='Arial, sans-serif')
    )

    # Update layout properties
    fig.update_layout(
        legend=dict(font=dict(color='white')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=0, b=0, l=10, r=10),
        width=600,
        height=600
    )

    # Save the pie chart as an image
    fig.write_image(path + filename)

    '''top_roles_count = 10 # Limit the DataFrame to only top roles and combine others into a single category
    if len(df) > top_roles_count:
        other_roles_count = df['Count'][top_roles_count:].sum()
        df = df[:top_roles_count]
        df.loc[len(df)] = ['Other roles', other_roles_count]

    fig = px.pie(df, values='Count', names='Role', title=title) # Create the pie chart
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=1)),  # Set border color and width
        textinfo='percent',  # Bold percentage values
        textfont=dict(color='white', size=12, family='Arial, sans-serif'),  # Set text color and size
    )
    fig.update_layout(
        legend=dict(font=dict(color='white')),  # Change legend text color to white
        paper_bgcolor='rgba(0,0,0,0)',  # Set transparent background
        plot_bgcolor='rgba(0,0,0,0)',  # Set transparent plot area background
        margin=dict(t=0, b=0, l=10, r=10),  # Remove unnecessary margins
        width=600, height=600,  # Set fixed width and height
    )

    fig.write_image(path+filename) # Save the pie chart as an image'''