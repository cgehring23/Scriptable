USE [BC130]
GO
/****** Object:  StoredProcedure [dbo].[GetShipmentData]    Script Date: 7/31/2023 8:47:09 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[GetShipmentData] @days INT
AS
BEGIN
    -- Generate the list of dates for the next @days days
    DECLARE @cols AS NVARCHAR(MAX),
            @query AS NVARCHAR(MAX);

    SELECT @cols = STUFF((SELECT ',' + QUOTENAME(CONVERT(DATE, DATEADD(day, number, GETDATE())))
                          FROM master..spt_values
                          WHERE type = 'P' AND number BETWEEN 0 AND @days - 1
                          FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '');

    -- Build the dynamic query
    SET @query = N'
    WITH ShipmentData AS (
        SELECT 
            [Document No_] AS SalesOrder,
            [No_],
            [Description],
			[Item Category Code],
            CASE 
                WHEN [LoadedOrders].[SalesOrder] IS NOT NULL THEN [LoadedOrders].[RolledDate]
                ELSE [Shipment Date]
            END AS ShipmentDate,
            SUM([Quantity]) AS Quantity
        FROM [BC130].[dbo].[Tucker Milling LLC$Sales Line]
        LEFT JOIN [10.0.0.17].[Products].[dbo].[LoadedOrders]
        ON [BC130].[dbo].[Tucker Milling LLC$Sales Line].[Document No_] COLLATE Latin1_General_100_CI_AS = [LoadedOrders].[SalesOrder] COLLATE Latin1_General_100_CI_AS
        WHERE [Document Type] = 1 AND [Posting Group] = ''INVT'' AND [No_] <> ''PALLET'' AND [Item Category Code] IN (''P-BAGGED'', ''P-DISTPROD'')
        GROUP BY [Document No_] COLLATE Latin1_General_100_CI_AS, [No_], [Description], [Item Category Code],
            CASE 
                WHEN [LoadedOrders].[SalesOrder] IS NOT NULL THEN [LoadedOrders].[RolledDate]
                ELSE [Shipment Date]
            END
    ),
    ShipmentData2 AS (
        SELECT 
            [Order No_] AS SalesOrder,
            [No_],
            [Description],
			[Item Category Code],
            CASE 
                WHEN [LoadedOrders].[SalesOrder] IS NOT NULL THEN [LoadedOrders].[RolledDate]
                ELSE [Shipment Date]
            END AS ShipmentDate,
            SUM([Quantity]) AS Quantity
        FROM [BC130].[dbo].[Tucker Milling LLC$Sales Invoice Line]
        LEFT JOIN [10.0.0.17].[Products].[dbo].[LoadedOrders]
        ON [BC130].[dbo].[Tucker Milling LLC$Sales Invoice Line].[Order No_] COLLATE Latin1_General_100_CI_AS = [LoadedOrders].[SalesOrder] COLLATE Latin1_General_100_CI_AS
        WHERE [BC130].[dbo].[Tucker Milling LLC$Sales Invoice Line].[Type] = 2 AND [Posting Group] = ''INVT'' AND [No_] <> ''PALLET'' AND [Item Category Code] IN (''P-BAGGED'', ''P-DISTPROD'')
        AND [Shipment Date] >= CAST(GETDATE() as date)
        GROUP BY [Order No_] COLLATE Latin1_General_100_CI_AS, [No_], [Description], [Item Category Code],
            CASE 
                WHEN [LoadedOrders].[SalesOrder] IS NOT NULL THEN [LoadedOrders].[RolledDate]
                ELSE [Shipment Date]
            END
    ),
    PivotData AS (
        SELECT *
        FROM ShipmentData
        PIVOT (
            SUM(Quantity)
            FOR [ShipmentDate] IN (' + @cols + ')
        ) AS PivotTable
    ),
    PivotData2 AS (
        SELECT *
        FROM ShipmentData2
        PIVOT (
            SUM(Quantity)
            FOR [ShipmentDate] IN (' + @cols + ')
        ) AS PivotTable
    )

    SELECT 
        ''Ordered'' AS ShipmentType,
        [SalesOrder],
        [No_],
        [Description], [Item Category Code], ' + STUFF((SELECT ', SUM(' + QUOTENAME(CONVERT(DATE, DATEADD(day, number, GETDATE()))) + ') AS ' + QUOTENAME(CONVERT(DATE, DATEADD(day, number, GETDATE())), '''')
                              FROM master..spt_values
                              WHERE type = 'P' AND number BETWEEN 0 AND @days - 1
                              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') + '
    FROM PivotData
    GROUP BY [SalesOrder], [No_], [Description], [Item Category Code]
    UNION ALL
    SELECT 
        CASE WHEN ([SalesOrder] IS NULL AND [No_] IS NULL AND [Description] IS NULL) THEN ''Grand Total'' ELSE ''Invoiced'' END AS ShipmentType,
        [SalesOrder],
        [No_],
        [Description], [Item Category Code], ' + STUFF((SELECT ', SUM(' + QUOTENAME(CONVERT(DATE, DATEADD(day, number, GETDATE()))) + ') AS ' + QUOTENAME(CONVERT(DATE, DATEADD(day, number, GETDATE())), '''')
                              FROM master..spt_values
                              WHERE type = 'P' AND number BETWEEN 0 AND @days - 1
                              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') + '
    FROM PivotData2
    GROUP BY [SalesOrder], [No_], [Description], [Item Category Code]
    ';

    -- Execute the dynamic query
    EXEC sp_executesql @query;
END;
